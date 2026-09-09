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
    [McpCommand("create_layer")]
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
        Guid parentLayerId = Guid.Empty;

        if (hasParent)
        {
            var matches = new List<Layer>();
            bool isFullPath = parent.Contains("::", StringComparison.Ordinal);

            foreach (var candidate in doc.Layers)
            {
                if (candidate.IsDeleted)
                    continue;

                string candidateReference = isFullPath ? candidate.FullPath : candidate.Name;
                if (string.Equals(candidateReference, parent, StringComparison.OrdinalIgnoreCase))
                    matches.Add(candidate);
            }

            if (matches.Count == 0)
                throw new InvalidOperationException(
                    $"Parent layer '{parent}' was not found. Use an existing layer name or exact full path (for example, 'Assembly::Left').");

            if (matches.Count > 1)
                throw new InvalidOperationException(
                    $"Parent layer name '{parent}' is ambiguous. Use the exact full path (for example, 'Assembly::Left').");

            parentLayerId = matches[0].Id;
        }

        if (hasName)
        {
            foreach (var candidate in doc.Layers)
            {
                if (!candidate.IsDeleted
                    && candidate.ParentLayerId == parentLayerId
                    && string.Equals(candidate.Name, name, StringComparison.OrdinalIgnoreCase))
                {
                    string location = hasParent ? $" under parent '{parent}'" : " at the document root";
                    throw new InvalidOperationException($"A sibling layer named '{name}' already exists{location}. Choose a different name.");
                }
            }
        }

        var layer = new Layer
        {
            ParentLayerId = parentLayerId
        };
        if (hasName) layer.Name = name;
        if (hasColor) layer.Color = Color.FromArgb(color[0], color[1], color[2]);

        var layerIndex = doc.Layers.Add(layer);
        if (layerIndex < 0)
            throw new InvalidOperationException($"Rhino could not create layer '{name ?? "(automatic name)"}'.");

        layer = doc.Layers.FindIndex(layerIndex);
        if (layer == null)
            throw new InvalidOperationException($"Rhino created layer index {layerIndex}, but the layer could not be retrieved.");

        // Update views
        doc.Views.Redraw();

        return Serializer.SerializeLayer(layer);
    }
}
