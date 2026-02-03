using System;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using System.Collections.Generic;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject SelectObjects(JObject parameters)
    {
        JObject filters = (JObject)parameters["filters"];

        var doc = RhinoDoc.ActiveDoc;
        var objects = doc.Objects.ToList();
        var selectedObjects = new List<Guid>();
        var filtersType = (string)parameters["filters_type"];

        var hasName = false;
        var hasColor = false;
        var customAttributes = new Dictionary<string, List<string>>();

        // no filter means all are selected
        if (filters.Count == 0)
        {
            doc.Objects.UnselectAll();
            doc.Objects.Select(objects.Select(o => o.Id));
            doc.Views.Redraw();

            return new JObject() { ["count"] = objects.Count };
        }

        foreach (JProperty f in filters.Properties())
        {
            if (f.Name == "name") hasName = true;
            if (f.Name == "color") hasColor = true;
            if (f.Name != "name" && f.Name != "color") customAttributes.Add(f.Name, castToStringList(f.Value));
        }

        var name = hasName ? castToString(filters.SelectToken("name")) : null;
        var color = hasColor ? castToIntArray(filters.SelectToken("color")) : null;

        if (filtersType == "and")
            foreach (var obj in objects)
            {
                var attributeMatch = true;
                if (hasName && obj.Name != name) continue;
                if (hasColor && (obj.Attributes.ObjectColor.R != color[0] || obj.Attributes.ObjectColor.G != color[1] || obj.Attributes.ObjectColor.B != color[2])) continue;
                foreach (var customAttribute in customAttributes)
                {
                    foreach (var value in customAttribute.Value)
                    {
                        if (obj.Attributes.GetUserString(customAttribute.Key) != value) attributeMatch = false;
                    }
                }
                if (!attributeMatch) continue;

                selectedObjects.Add(obj.Id);
            }
        else if (filtersType == "or")
            foreach (var obj in objects)
            {
                var attributeMatch = false;
                if (hasName && obj.Name == name) attributeMatch = true;
                if (hasColor && obj.Attributes.ObjectColor.R == color[0] && obj.Attributes.ObjectColor.G == color[1] && obj.Attributes.ObjectColor.B == color[2]) attributeMatch = true;

                foreach (var customAttribute in customAttributes)
                {
                    foreach (var value in customAttribute.Value)
                    {
                        if (obj.Attributes.GetUserString(customAttribute.Key) == value) attributeMatch = true;
                    }
                }
                if (!attributeMatch) continue;

                selectedObjects.Add(obj.Id);
            }

        doc.Objects.UnselectAll();
        doc.Objects.Select(selectedObjects);
        doc.Views.Redraw();

        return new JObject() { ["count"] = selectedObjects.Count };
    }
}