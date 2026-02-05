using System;
using System.Collections.Generic;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoMCP.Shared.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
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
        if (hasGuid) layer = doc.Layers.FindId(Guid.Parse(guid));

        if (layer == null)
        {
            return new JObject
            {
                ["success"] = false,
                ["message"] = "Layer not found"
            };
        }
        if (layer == null)
        {
            return new JObject
            {
                ["success"] = false,
                ["message"] = "Layer not found"
            };
        }

        name = layer.Name;
        doc.Layers.Delete(layer.Index, true);

        // Update views
        doc.Views.Redraw();

        return new JObject
        {
            ["success"] = true,
            ["message"] = $"Layer {name} deleted"
        };
    }
}