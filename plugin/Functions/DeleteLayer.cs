using System;
using System.Collections.Generic;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("delete_layer")]
    public JObject DeleteLayer(JObject parameters)
    {
        // parse meta data
        bool hasName = parameters.ContainsKey("name");
        bool hasGuid = parameters.ContainsKey("guid");

        string name = hasName ? castToString(parameters.SelectToken("name")) : null;
        string guid = hasGuid ? castToString(parameters.SelectToken("guid")) : null;

        var doc = RhinoDoc.ActiveDoc;

        Layer layer = null;
        if (hasName) layer = doc.Layers.FindName(name);
        if (hasGuid) layer = doc.Layers.FindId(McpException.ParseGuid(guid));

        if (layer == null || layer.IsDeleted) throw McpException.LayerNotFound(hasGuid ? guid : name);

        name = layer.Name;
        // Rhino refuses some deletes (the current layer, one that still holds
        // objects) and says so only through the return value; reporting success
        // regardless told the agent something false (issue #86).
        if (!doc.Layers.Delete(layer.Index, true))
            throw LayerDeleteRefused(doc, layer);

        // Update views
        doc.Views.Redraw();

        return new JObject
        {
            ["success"] = true,
            ["message"] = $"Layer {name} deleted"
        };
    }

    private static McpException LayerDeleteRefused(RhinoDoc doc, Layer layer)
    {
        string path = layer.FullPath ?? layer.Name;
        if (doc.Layers.CurrentLayerIndex == layer.Index)
            return new McpException(
                McpException.InvalidArgument,
                $"Rhino did not delete layer '{path}': it is the current layer",
                "Make another layer current with get_or_set_current_layer, then call delete_layer again.");

        int objectCount = doc.Objects.FindByLayer(layer)?.Length ?? 0;
        int childCount = layer.GetChildren()?.Length ?? 0;
        if (objectCount > 0 || childCount > 0)
        {
            string holds = objectCount > 0 && childCount > 0
                ? $"{objectCount} object(s) and {childCount} sublayer(s)"
                : objectCount > 0 ? $"{objectCount} object(s)" : $"{childCount} sublayer(s)";
            return new McpException(
                McpException.InvalidArgument,
                $"Rhino did not delete layer '{path}': it still holds {holds}",
                "Delete the objects or move them to another layer (update_object_attributes with layer), and delete or move its sublayers, then call delete_layer again.");
        }

        return new McpException(
            McpException.RhinoError,
            $"Rhino did not delete layer '{path}'",
            "Check in Rhino whether the layer is locked, a reference (worksession) layer, or in use by a block definition.");
    }
}
