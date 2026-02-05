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
    public JObject CreateLayer(JObject parameters)
    {
        // parse meta data
        bool hasName = parameters.ContainsKey("name");
        bool hasColor = parameters.ContainsKey("color");
        bool hasParent = parameters.ContainsKey("parent");

        string name = hasName ? castToString(parameters.SelectToken("name")) : null;
        int[] color = hasColor ? castToIntArray(parameters.SelectToken("color")) : null;
        string parent = hasParent ? castToString(parameters.SelectToken("parent")) : null;

        var doc = RhinoDoc.ActiveDoc;

        var layer = new Layer();
        if (hasName) layer.Name = name;
        if (hasColor) layer.Color = Color.FromArgb(color[0], color[1], color[2]);

        if (hasParent)
        {
            var parentLayer = doc.Layers.FindName(parent);
            if (parentLayer != null)
                layer.ParentLayerId = parentLayer.Id;

        }
        // Create a box centered at the specified point
        var layerId = doc.Layers.Add(layer);
        layer = doc.Layers.FindIndex(layerId);

        // Update views
        doc.Views.Redraw();

        return Serializer.SerializeLayer(layer);
    }
}