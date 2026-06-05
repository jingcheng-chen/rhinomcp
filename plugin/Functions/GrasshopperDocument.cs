using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_create_document")]
    public JObject GhCreateDocument(JObject parameters)
    {
        bool newIfMissing = OptionalBool(parameters, "new_if_missing", true);
        bool makeActive = OptionalBool(parameters, "make_active", true);
        bool openCanvas = OptionalBool(parameters, "open_canvas", true);

        if (openCanvas && Instances.ActiveCanvas == null)
        {
            RhinoApp.RunScript("_Grasshopper", false);
            RhinoApp.Wait();
        }

        var server = Instances.DocumentServer;
        var canvas = Instances.ActiveCanvas;
        var doc = canvas?.Document;
        bool created = false;

        if (doc == null && server.DocumentCount > 0)
        {
            doc = server.NextAvailableDocument();
            if (doc == null && server.DocumentCount == 1)
            {
                doc = server[0];
            }
        }

        if (doc == null && newIfMissing)
        {
            doc = server.AddNewDocument();
            created = doc != null;
        }

        if (doc != null && makeActive)
        {
            server.PromoteDocument(doc);
            if (Instances.ActiveCanvas != null)
            {
                Instances.ActiveCanvas.Document = doc;
            }
            RedrawGrasshopperCanvas();
        }

        bool hasDocument = doc != null;
        return new JObject
        {
            ["has_document"] = hasDocument,
            ["created"] = created,
            ["made_active"] = hasDocument && makeActive,
            ["canvas_open"] = Instances.ActiveCanvas != null,
            ["file_path"] = doc?.FilePath ?? (hasDocument ? "(unsaved)" : null),
            ["object_count"] = doc?.ObjectCount ?? 0,
            ["visibility"] = hasDocument ? GrasshopperVisibilityState(doc) : null,
            ["message"] = hasDocument
                ? (created ? "Created Grasshopper document" : "Grasshopper document is available")
                : "No active Grasshopper document"
        };
    }

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
            ["visibility"] = GrasshopperVisibilityState(doc),
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
            AddSpecialGrasshopperState(compInfo, component);
            AddGraphMetadataFields(compInfo, component);
            components.Add(compInfo);
        }

        var standaloneParams = new JArray();
        foreach (var param in doc.Objects.OfType<IGH_Param>()
                     .Where(p => p.Attributes?.GetTopLevel.DocObject is not IGH_Component))
        {
            var paramInfo = new JObject
            {
                ["instance_id"] = param.InstanceGuid.ToString(),
                ["name"] = param.Name,
                ["nickname"] = param.NickName,
                ["type"] = param.TypeName,
                ["position"] = PivotToJson(param),
                ["source_count"] = param.SourceCount,
                ["recipient_count"] = param.Recipients.Count
            };
            AddSpecialGrasshopperState(paramInfo, param);
            AddGraphMetadataFields(paramInfo, param);
            if (includeValues)
            {
                paramInfo["value_data"] = ParamVolatileDataToJson(param, maxItems);
            }
            standaloneParams.Add(paramInfo);
        }

        var groups = new JArray(doc.Objects.OfType<GH_Group>().Select(g =>
        {
            var groupInfo = new JObject
            {
                ["instance_id"] = g.InstanceGuid.ToString(),
                ["nickname"] = g.NickName,
                ["object_count"] = g.ObjectIDs.Count
            };
            AddGraphMetadataFields(groupInfo, g);
            return groupInfo;
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
            ["groups"] = groups,
            ["visibility"] = GrasshopperVisibilityState(doc)
        };
    }
}
