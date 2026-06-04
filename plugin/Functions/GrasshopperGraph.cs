using System;
using System.Diagnostics;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_get_graph", ReadOnly = true)]
    public JObject GhGetGraph(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        string graphId = OptionalString(parameters, "graph_id");
        if (string.IsNullOrWhiteSpace(graphId))
        {
            throw new ArgumentException("graph_id is required.");
        }

        bool includeValues = OptionalBool(parameters, "include_values", false);
        int maxItems = Clamp(OptionalInt(parameters, "max_items", 20), 0, 1000);
        var objects = GetGraphObjects(doc, graphId);
        var components = new JArray();
        var standaloneParams = new JArray();
        var groups = new JArray();

        foreach (var obj in objects)
        {
            if (obj is IGH_Component component)
            {
                var item = new JObject
                {
                    ["instance_id"] = component.InstanceGuid.ToString(),
                    ["name"] = component.Name,
                    ["nickname"] = component.NickName,
                    ["category"] = component.Category,
                    ["subcategory"] = component.SubCategory,
                    ["position"] = PivotToJson(component),
                    ["runtime_message_level"] = component.RuntimeMessageLevel.ToString(),
                    ["inputs"] = ParamsToJson(component.Params.Input, includeSources: true, includeValues, maxItems),
                    ["outputs"] = ParamsToJson(component.Params.Output, includeSources: true, includeValues, maxItems),
                    ["runtime_messages"] = RuntimeMessagesToJson(component)
                };
                AddSpecialGrasshopperState(item, component);
                AddGraphMetadataFields(item, component);
                components.Add(item);
            }
            else if (obj is GH_Group group)
            {
                var item = new JObject
                {
                    ["instance_id"] = group.InstanceGuid.ToString(),
                    ["nickname"] = group.NickName,
                    ["object_count"] = group.ObjectIDs.Count
                };
                AddGraphMetadataFields(item, group);
                groups.Add(item);
            }
            else if (obj is IGH_Param param)
            {
                var item = new JObject
                {
                    ["instance_id"] = param.InstanceGuid.ToString(),
                    ["name"] = param.Name,
                    ["nickname"] = param.NickName,
                    ["type"] = param.TypeName,
                    ["position"] = PivotToJson(param),
                    ["source_count"] = param.SourceCount,
                    ["recipient_count"] = param.Recipients.Count
                };
                AddSpecialGrasshopperState(item, param);
                AddGraphMetadataFields(item, param);
                if (includeValues)
                {
                    item["value_data"] = ParamVolatileDataToJson(param, maxItems);
                }
                standaloneParams.Add(item);
            }
        }

        return new JObject
        {
            ["graph_id"] = graphId,
            ["object_count"] = objects.Count,
            ["component_count"] = components.Count,
            ["standalone_parameter_count"] = standaloneParams.Count,
            ["group_count"] = groups.Count,
            ["components"] = components,
            ["standalone_parameters"] = standaloneParams,
            ["groups"] = groups,
            ["summary"] = BuildGraphSummary(doc, objects, graphId, null)
        };
    }

    [McpCommand("gh_clear_graph")]
    public JObject GhClearGraph(JObject parameters)
    {
        var stopwatch = Stopwatch.StartNew();
        var doc = GetActiveGrasshopperDocument();
        string graphId = OptionalString(parameters, "graph_id");
        if (string.IsNullOrWhiteSpace(graphId))
        {
            throw new ArgumentException("graph_id is required.");
        }

        bool includeGroups = OptionalBool(parameters, "include_groups", true);
        bool recompute = OptionalBool(parameters, "recompute", false);
        var objects = GetGraphObjects(doc, graphId)
            .Where(o => includeGroups || o is not GH_Group)
            .ToList();

        int deletedGroupCount = objects.Count(o => o is GH_Group);
        int deletedComponentCount = objects.Count(o => o is IGH_Component || o is IGH_Param);
        doc.RemoveObjects(objects, false);

        long solutionDurationMs = 0;
        if (recompute)
        {
            var solutionStopwatch = Stopwatch.StartNew();
            RunGrasshopperSolution(doc, false);
            solutionStopwatch.Stop();
            solutionDurationMs = solutionStopwatch.ElapsedMilliseconds;
        }

        stopwatch.Stop();
        return new JObject
        {
            ["graph_id"] = graphId,
            ["deleted_count"] = objects.Count,
            ["deleted_component_count"] = deletedComponentCount,
            ["deleted_group_count"] = deletedGroupCount,
            ["include_groups"] = includeGroups,
            ["recomputed"] = recompute,
            ["solution_duration_ms"] = solutionDurationMs,
            ["duration_ms"] = stopwatch.ElapsedMilliseconds,
            ["message"] = $"Cleared {objects.Count} Grasshopper object(s) from graph '{graphId}'"
        };
    }
}
