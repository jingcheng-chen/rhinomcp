using System;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using System.Collections.Generic;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("select_objects")]
    public JObject SelectObjects(JObject parameters)
    {
        JObject filters = (JObject)parameters["filters"] ?? new JObject();

        var doc = RhinoDoc.ActiveDoc;
        var filtersType = (string)parameters["filters_type"] ?? "and";

        if (filtersType != "and" && filtersType != "or")
            throw new InvalidOperationException($"Invalid filters_type '{filtersType}': expected 'and' or 'or'.");

        // filters.name, ids and type are lists (type may also be one string);
        // color is a single RGB triplet; layer is one full layer path; hidden and
        // locked are booleans. Any other key is a custom user-string attribute
        // (see contracts/commands/select_objects.json).
        List<string> nameValues = null;
        int[] color = null;
        HashSet<Guid> ids = null;
        Layer layer = null;
        HashSet<string> types = null;
        bool? hidden = null;
        bool? locked = null;
        var customAttributes = new Dictionary<string, List<string>>();

        foreach (JProperty f in filters.Properties())
        {
            switch (f.Name)
            {
                case "name":
                    nameValues = castToStringList(f.Value);
                    break;
                case "color":
                    color = castToIntArray(f.Value);
                    break;
                case "ids":
                    ids = new HashSet<Guid>();
                    foreach (var text in castToStringList(f.Value))
                    {
                        var id = McpException.ParseGuid(text);
                        if (doc.Objects.FindId(id) == null) throw McpException.ObjectNotFound(text);
                        ids.Add(id);
                    }
                    break;
                case "layer":
                    var layerPath = castToString(f.Value);
                    layer = FindLayerByNameOrFullPath(doc, layerPath);
                    if (layer == null) throw McpException.LayerNotFound(layerPath);
                    break;
                case "type":
                    var typeList = f.Value.Type == JTokenType.Array
                        ? castToStringList(f.Value)
                        : new List<string> { castToString(f.Value) };
                    types = new HashSet<string>(typeList.Select(t => t.ToUpperInvariant()));
                    break;
                case "hidden":
                    hidden = castToBool(f.Value);
                    break;
                case "locked":
                    locked = castToBool(f.Value);
                    break;
                default:
                    customAttributes[f.Name] = castToStringList(f.Value);
                    break;
            }
        }

        bool IsHidden(RhinoObject obj) => obj.IsHidden || !doc.Layers[obj.Attributes.LayerIndex].IsVisible;

        // One check per present built-in key; each custom attribute is one more.
        var checks = new List<Func<RhinoObject, bool>>();
        if (nameValues != null) checks.Add(obj => nameValues.Contains(obj.Name));
        if (color != null) checks.Add(obj =>
            obj.Attributes.ObjectColor.R == color[0] &&
            obj.Attributes.ObjectColor.G == color[1] &&
            obj.Attributes.ObjectColor.B == color[2]);
        if (ids != null) checks.Add(obj => ids.Contains(obj.Id));
        if (layer != null) checks.Add(obj => obj.Attributes.LayerIndex == layer.Index);
        if (types != null) checks.Add(obj => types.Contains(GetNormalizedType(obj)));
        if (hidden.HasValue) checks.Add(obj => IsHidden(obj) == hidden.Value);
        if (locked.HasValue) checks.Add(obj => IsObjectOrLayerLocked(doc, obj) == locked.Value);
        foreach (var customAttribute in customAttributes)
        {
            var key = customAttribute.Key;
            var values = customAttribute.Value;
            checks.Add(obj =>
            {
                var userValue = obj.Attributes.GetUserString(key);
                return userValue != null && values.Contains(userValue);
            });
        }

        // Hidden and locked objects (or objects on hidden or locked layers) are
        // candidates only when the filter asks for them.
        var settings = new ObjectEnumeratorSettings
        {
            NormalObjects = true,
            HiddenObjects = hidden == true,
            LockedObjects = locked == true,
        };

        var matched = new List<RhinoObject>();
        foreach (var obj in doc.Objects.GetObjectList(settings))
        {
            bool selected;
            if (checks.Count == 0) selected = true;  // no filter means all are selected
            else if (filtersType == "and") selected = checks.All(check => check(obj));
            else selected = checks.Any(check => check(obj));

            if (selected) matched.Add(obj);
        }

        // Rhino refuses to select an object that is itself hidden or locked; an
        // object only on a hidden or locked layer was asked for, so allow it.
        doc.Objects.UnselectAll();
        int count = 0;
        foreach (var obj in matched)
        {
            if (obj.Select(true, true, true, false, true, true) > 0) count++;
        }
        doc.Views.Redraw();

        return new JObject() { ["count"] = count, ["matched"] = matched.Count };
    }
}
