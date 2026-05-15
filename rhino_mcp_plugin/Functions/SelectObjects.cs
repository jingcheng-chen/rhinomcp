using System;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using System.Collections.Generic;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("select_objects")]
    public JObject SelectObjects(JObject parameters)
    {
        JObject filters = (JObject)parameters["filters"];

        var doc = RhinoDoc.ActiveDoc;
        var objects = doc.Objects.ToList();
        var selectedObjects = new List<Guid>();
        var filtersType = (string)parameters["filters_type"] ?? "and";

        if (filtersType != "and" && filtersType != "or")
            throw new InvalidOperationException($"Invalid filters_type '{filtersType}': expected 'and' or 'or'.");

        // no filter means all are selected
        if (filters.Count == 0)
        {
            doc.Objects.UnselectAll();
            doc.Objects.Select(objects.Select(o => o.Id));
            doc.Views.Redraw();

            return new JObject() { ["count"] = objects.Count };
        }

        // filters.name is documented as a list of strings; custom attributes are also lists.
        // color stays a single RGB triplet (see contracts/commands/select_objects.json).
        List<string> nameValues = null;
        int[] color = null;
        var customAttributes = new Dictionary<string, List<string>>();

        foreach (JProperty f in filters.Properties())
        {
            if (f.Name == "name") nameValues = castToStringList(f.Value);
            else if (f.Name == "color") color = castToIntArray(f.Value);
            else customAttributes[f.Name] = castToStringList(f.Value);
        }

        bool hasName = nameValues != null;
        bool hasColor = color != null;

        bool ColorMatches(Rhino.DocObjects.RhinoObject obj) =>
            obj.Attributes.ObjectColor.R == color[0] &&
            obj.Attributes.ObjectColor.G == color[1] &&
            obj.Attributes.ObjectColor.B == color[2];

        foreach (var obj in objects)
        {
            bool selected;
            if (filtersType == "and")
            {
                // Each present filter key must match at least one of its listed values.
                selected = true;
                if (hasName && !nameValues.Contains(obj.Name)) selected = false;
                if (selected && hasColor && !ColorMatches(obj)) selected = false;
                if (selected)
                {
                    foreach (var customAttribute in customAttributes)
                    {
                        var userValue = obj.Attributes.GetUserString(customAttribute.Key);
                        if (userValue == null || !customAttribute.Value.Contains(userValue))
                        {
                            selected = false;
                            break;
                        }
                    }
                }
            }
            else
            {
                // Any present filter key matching any listed value wins.
                selected = false;
                if (hasName && nameValues.Contains(obj.Name)) selected = true;
                if (!selected && hasColor && ColorMatches(obj)) selected = true;
                if (!selected)
                {
                    foreach (var customAttribute in customAttributes)
                    {
                        var userValue = obj.Attributes.GetUserString(customAttribute.Key);
                        if (userValue != null && customAttribute.Value.Contains(userValue))
                        {
                            selected = true;
                            break;
                        }
                    }
                }
            }

            if (selected) selectedObjects.Add(obj.Id);
        }

        doc.Objects.UnselectAll();
        doc.Objects.Select(selectedObjects);
        doc.Views.Redraw();

        return new JObject() { ["count"] = selectedObjects.Count };
    }
}