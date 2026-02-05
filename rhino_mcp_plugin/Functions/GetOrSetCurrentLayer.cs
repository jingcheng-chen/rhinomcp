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
    public JObject GetOrSetCurrentLayer(JObject parameters)
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

        if (layer != null) doc.Layers.SetCurrentLayerIndex(layer.Index, true);
        else layer = doc.Layers.CurrentLayer;

        // Update views
        doc.Views.Redraw();

        return Serializer.SerializeLayer(layer);
    }
}