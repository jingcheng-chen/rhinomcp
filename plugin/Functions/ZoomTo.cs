using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    // Frame the named (or active) viewport on all visible objects, the selection,
    // given ids or a layer. ReadOnly so no undo record is opened: framing is a
    // view change, not a document edit.
    [McpCommand("zoom_to", ReadOnly = true)]
    public JObject ZoomTo(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var covered = ZoomTargets(doc, parameters);
        var view = ResolveCameraView(doc, parameters);

        var bbox = BoundingBox.Empty;
        foreach (var obj in covered)
            bbox.Union(obj.Geometry.GetBoundingBox(true));
        if (covered.Count == 0 || !bbox.IsValid)
            throw new McpException(
                McpException.InvalidArgument,
                "Nothing to zoom to: the target covers no visible objects",
                "Create or show objects first, or pick another target.");

        // A point or a flat object has a degenerate box, which ZoomBoundingBox
        // cannot frame; pad it so the camera has something to fit.
        var framed = bbox;
        if (framed.Diagonal.Length < RhinoMath.SqrtEpsilon)
            framed.Inflate(1.0);

        var viewport = view.ActiveViewport;
        viewport.ZoomBoundingBox(framed);
        view.Redraw();

        var state = CameraState(viewport);
        state["bounding_box"] = new JObject
        {
            ["min"] = new JArray(bbox.Min.X, bbox.Min.Y, bbox.Min.Z),
            ["max"] = new JArray(bbox.Max.X, bbox.Max.Y, bbox.Max.Z),
        };
        state["object_count"] = covered.Count;
        return state;
    }

    private List<RhinoObject> ZoomTargets(RhinoDoc doc, JObject parameters)
    {
        string target = castToString(parameters["target"]);
        foreach (var kind in new[] { "object_ids", "layer" })
        {
            if (target == kind && !HasValue(parameters, kind))
                throw new McpException(
                    McpException.InvalidArgument,
                    $"target '{kind}' needs {kind}",
                    $"Pass {kind}, or use target 'all' or 'selection'.");
        }

        switch (target)
        {
            case "all":
                return doc.Objects.GetObjectList(new ObjectEnumeratorSettings
                {
                    VisibleFilter = true,
                    NormalObjects = true,
                    LockedObjects = true,
                }).ToList();

            case "selection":
                var selected = doc.Objects.GetSelectedObjects(false, false).ToList();
                if (selected.Count == 0)
                    throw new McpException(
                        McpException.InvalidArgument,
                        "Nothing is selected to zoom to",
                        "Select objects first with select_objects, or use target 'all', 'object_ids' or 'layer'.");
                return selected;

            case "object_ids":
                var found = new List<RhinoObject>();
                foreach (var idText in castToStringList(parameters["object_ids"]))
                {
                    var obj = doc.Objects.Find(McpException.ParseGuid(idText));
                    if (obj == null)
                        throw McpException.ObjectNotFound(idText);
                    found.Add(obj);
                }
                return found;

            case "layer":
                string layerName = castToString(parameters["layer"]);
                var layer = FindLayerByNameOrFullPath(doc, layerName)
                    ?? throw McpException.LayerNotFound(layerName);
                return (doc.Objects.FindByLayer(layer) ?? new RhinoObject[0])
                    .Where(o => o.Visible)
                    .ToList();

            default:
                throw new McpException(
                    McpException.InvalidArgument,
                    $"Unknown zoom target '{target}'",
                    "Pass target 'all', 'selection', 'object_ids' or 'layer'.");
        }
    }

    // Present and non-empty: a missing key, null, "" and [] all count as absent.
    private static bool HasValue(JObject parameters, string name)
    {
        var token = parameters[name];
        if (token == null || token.Type == JTokenType.Null) return false;
        if (token.Type == JTokenType.String) return token.ToString().Length > 0;
        if (token.Type == JTokenType.Array) return token.HasValues;
        return true;
    }
}
