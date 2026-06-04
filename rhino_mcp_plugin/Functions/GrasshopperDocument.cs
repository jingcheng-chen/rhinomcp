using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_get_document_info", ReadOnly = true)]
    public JObject GhGetDocumentInfo(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument(required: false);
        if (doc == null)
        {
            return new JObject
            {
                ["has_document"] = false,
                ["message"] = "No active Grasshopper document"
            };
        }

        var componentsByCategory = doc.Objects
            .OfType<IGH_Component>()
            .GroupBy(c => c.Category ?? "Unknown")
            .ToDictionary(g => g.Key, g => g.Count());

        return new JObject
        {
            ["has_document"] = true,
            ["file_path"] = doc.FilePath ?? "(unsaved)",
            ["is_modified"] = doc.IsModified,
            ["object_count"] = doc.ObjectCount,
            ["component_count"] = doc.Objects.OfType<IGH_Component>().Count(),
            ["parameter_count"] = doc.Objects.OfType<IGH_Param>()
                .Count(p => p.Attributes?.GetTopLevel.DocObject is not IGH_Component),
            ["group_count"] = doc.Objects.OfType<GH_Group>().Count(),
            ["components_by_category"] = JObject.FromObject(componentsByCategory)
        };
    }

    [McpCommand("gh_get_canvas_state", ReadOnly = true)]
    public JObject GhGetCanvasState(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool includeConnections = OptionalBool(parameters, "include_connections", true);
        bool includeValues = OptionalBool(parameters, "include_values", false);
        int maxItems = Clamp(OptionalInt(parameters, "max_items", 20), 0, 1000);

        var components = new JArray();
        foreach (var component in doc.Objects.OfType<IGH_Component>())
        {
            var compInfo = new JObject
            {
                ["instance_id"] = component.InstanceGuid.ToString(),
                ["name"] = component.Name,
                ["nickname"] = component.NickName,
                ["category"] = component.Category,
                ["subcategory"] = component.SubCategory,
                ["position"] = PivotToJson(component),
                ["runtime_message_level"] = component.RuntimeMessageLevel.ToString(),
                ["inputs"] = ParamsToJson(component.Params.Input, includeConnections, includeValues, maxItems),
                ["outputs"] = ParamsToJson(component.Params.Output, includeConnections, includeValues, maxItems)
            };
            components.Add(compInfo);
        }

        var standaloneParams = new JArray();
        foreach (var param in doc.Objects.OfType<IGH_Param>()
                     .Where(p => p.Attributes?.GetTopLevel.DocObject is not IGH_Component))
        {
            standaloneParams.Add(new JObject
            {
                ["instance_id"] = param.InstanceGuid.ToString(),
                ["name"] = param.Name,
                ["nickname"] = param.NickName,
                ["type"] = param.TypeName,
                ["position"] = PivotToJson(param),
                ["source_count"] = param.SourceCount,
                ["recipient_count"] = param.Recipients.Count
            });
        }

        var groups = new JArray(doc.Objects.OfType<GH_Group>().Select(g => new JObject
        {
            ["instance_id"] = g.InstanceGuid.ToString(),
            ["nickname"] = g.NickName,
            ["object_count"] = g.ObjectIDs.Count
        }));

        return new JObject
        {
            ["file_path"] = doc.FilePath ?? "(unsaved)",
            ["object_count"] = doc.ObjectCount,
            ["component_count"] = components.Count,
            ["standalone_parameter_count"] = standaloneParams.Count,
            ["group_count"] = groups.Count,
            ["components"] = components,
            ["standalone_parameters"] = standaloneParams,
            ["groups"] = groups
        };
    }
}
