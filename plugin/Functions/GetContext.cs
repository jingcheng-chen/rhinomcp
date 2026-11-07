using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    private const int ContextTypeCap = 8;
    private const int ContextSelectedIdCap = 20;
    private static readonly Guid GrasshopperPluginId = new Guid("b45a29b1-4343-4035-989e-044e8580d9cf");

    // Bounded grounding snapshot of the active document and active viewport.
    // Reads only: no selection, view or document state is changed.
    [McpCommand("get_context", ReadOnly = true)]
    public JObject GetContext(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        // Same enumeration as get_document_summary, so counts agree.
        var typeCounts = new Dictionary<string, int>();
        BoundingBox sceneBbox = BoundingBox.Empty;
        int objectCount = 0;
        foreach (var obj in doc.Objects)
        {
            objectCount++;
            string objType = GetNormalizedType(obj);
            typeCounts[objType] = typeCounts.TryGetValue(objType, out int n) ? n + 1 : 1;
            sceneBbox.Union(obj.Geometry.GetBoundingBox(true));
        }

        var objectsByType = new JObject();
        foreach (var kvp in typeCounts.OrderByDescending(x => x.Value).Take(ContextTypeCap))
        {
            objectsByType[kvp.Key] = kvp.Value;
        }

        var selected = doc.Objects.GetSelectedObjects(false, false).ToList();
        var selectedIds = new JArray(selected.Take(ContextSelectedIdCap).Select(o => o.Id.ToString()));

        return new JObject
        {
            ["document_name"] = string.IsNullOrEmpty(doc.Name) ? null : doc.Name,
            ["document_path"] = string.IsNullOrEmpty(doc.Path) ? null : doc.Path,
            ["units"] = doc.ModelUnitSystem.ToString(),
            ["absolute_tolerance"] = doc.ModelAbsoluteTolerance,
            ["angle_tolerance"] = doc.ModelAngleToleranceDegrees,
            ["current_layer"] = doc.Layers.CurrentLayer.FullPath,
            ["layer_count"] = doc.Layers.ActiveCount,
            ["object_count"] = objectCount,
            ["objects_by_type"] = objectsByType,
            ["selection_count"] = selected.Count,
            ["selected_ids"] = selectedIds,
            ["viewport"] = SerializeActiveViewport(doc),
            ["scene_bounding_box"] = SerializeMinMax(sceneBbox),
            ["grasshopper_definition_count"] = CountGrasshopperDefinitions(),
        };
    }

    private static JObject SerializeActiveViewport(RhinoDoc doc)
    {
        var viewport = doc.Views.ActiveView?.ActiveViewport
            ?? throw new McpException(
                McpException.NotFound, "No active viewport", "Open a model view in Rhino, then retry.");
        // The shared viewport state, plus "name", which get_context reported
        // before the state was shared.
        var state = ViewportState(viewport);
        state.AddFirst(new JProperty("name", viewport.Name));
        return state;
    }

    // Grasshopper is only asked when its plugin is already loaded, so reading the
    // context never loads Grasshopper as a side effect.
    private static int CountGrasshopperDefinitions()
    {
        try
        {
            Rhino.PlugIns.PlugIn.PlugInExists(GrasshopperPluginId, out bool loaded, out bool _);
            return loaded ? LoadedGrasshopperDocumentCount() : 0;
        }
        catch (Exception)
        {
            return 0;
        }
    }

    // Kept out of line so the Grasshopper assembly is touched only when it is loaded.
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static int LoadedGrasshopperDocumentCount()
    {
        return Grasshopper.Instances.DocumentServer?.DocumentCount ?? 0;
    }
}
