using System;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("get_object_attributes", ReadOnly = true)]
    public JObject GetObjectAttributes(JObject parameters)
    {
        var obj = getObjectByIdOrName(parameters);
        return SerializeObjectAttributes(obj);
    }

    [McpCommand("update_object_attributes")]
    public JObject UpdateObjectAttributes(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        if (!HasObjectAttributeUpdates(parameters))
            throw new ArgumentException("update_object_attributes requires at least one attribute update.");

        var obj = getObjectByIdOrName(parameters);
        var attrs = obj.Attributes;
        var attributesModified = false;

        if (parameters["visible"]?.Type == JTokenType.Boolean &&
            parameters["locked"]?.Type == JTokenType.Boolean &&
            parameters["visible"]!.ToObject<bool>() == false &&
            parameters["locked"]!.ToObject<bool>() == true)
        {
            throw new InvalidOperationException("Object cannot be hidden and locked at the same time.");
        }
        if (parameters["visible"]?.Type == JTokenType.Boolean &&
            parameters["visible"]!.ToObject<bool>() == false &&
            obj.IsLocked &&
            parameters["locked"]?.ToObject<bool>() != false)
        {
            throw new InvalidOperationException("Locked objects cannot be hidden; set locked=false in the same update.");
        }

        if (parameters["new_name"] != null)
        {
            attrs.Name = parameters["new_name"]!.ToString();
            attributesModified = true;
        }

        if (parameters["layer"] != null)
        {
            var layerName = parameters["layer"]!.ToString();
            var layer = FindLayerByNameOrFullPath(doc, layerName);
            if (layer == null)
                throw new InvalidOperationException($"Layer '{layerName}' not found.");

            attrs.LayerIndex = layer.Index;
            attributesModified = true;
        }

        if (parameters["color"] != null)
        {
            var color = parameters["color"]!.ToObject<int[]>() ?? new[] { 0, 0, 0 };
            attrs.ObjectColor = Color.FromArgb(color[0], color[1], color[2]);
            attrs.ColorSource = ObjectColorSource.ColorFromObject;
            attributesModified = true;
        }

        if (parameters["material_index"] != null)
        {
            var materialIndex = parameters["material_index"]!.ToObject<int>();
            if (materialIndex < -1 || materialIndex >= doc.Materials.Count)
                throw new InvalidOperationException($"Material index {materialIndex} is outside the document material table.");

            attrs.MaterialIndex = materialIndex;
            attrs.MaterialSource = materialIndex == -1
                ? ObjectMaterialSource.MaterialFromLayer
                : ObjectMaterialSource.MaterialFromObject;
            attributesModified = true;
        }

        if (parameters["clear_user_strings"]?.ToObject<bool>() == true)
        {
            foreach (var key in attrs.GetUserStrings().AllKeys)
            {
                attrs.SetUserString(key, null);
            }
            attributesModified = true;
        }

        if (parameters["delete_user_strings"] is JArray deleteKeys)
        {
            foreach (var keyToken in deleteKeys)
            {
                var key = keyToken.ToString();
                if (!string.IsNullOrEmpty(key))
                {
                    attrs.SetUserString(key, null);
                    attributesModified = true;
                }
            }
        }

        if (parameters["user_strings"] is JObject userStrings)
        {
            foreach (var property in userStrings.Properties())
            {
                if (string.IsNullOrEmpty(property.Name))
                    throw new InvalidOperationException("User string keys cannot be empty.");

                if (property.Value.Type == JTokenType.Null)
                {
                    attrs.SetUserString(property.Name, null);
                }
                else if (property.Value.Type == JTokenType.String)
                {
                    attrs.SetUserString(property.Name, property.Value.ToString());
                }
                else if (property.Value.Type == JTokenType.Integer ||
                         property.Value.Type == JTokenType.Float ||
                         property.Value.Type == JTokenType.Boolean)
                {
                    attrs.SetUserString(property.Name, property.Value.ToString(Formatting.None));
                }
                else
                {
                    throw new InvalidOperationException("User string values must be strings, numbers, booleans, or null.");
                }
                attributesModified = true;
            }
        }

        if (attributesModified)
        {
            doc.Objects.ModifyAttributes(obj, attrs, true);
        }

        var id = obj.Id;

        // Rhino object visibility and lock state are object table operations.
        // Locked objects are visible in Rhino, so locking a hidden object shows it first.
        if (parameters["locked"]?.Type == JTokenType.Boolean &&
            parameters["locked"]!.ToObject<bool>() == false)
        {
            doc.Objects.Unlock(id, false);
        }

        if (parameters["visible"]?.Type == JTokenType.Boolean &&
            parameters["visible"]!.ToObject<bool>() == true)
        {
            doc.Objects.Show(id, false);
        }

        if (parameters["visible"]?.Type == JTokenType.Boolean &&
            parameters["visible"]!.ToObject<bool>() == false)
        {
            doc.Objects.Hide(id, false);
        }

        if (parameters["locked"]?.Type == JTokenType.Boolean &&
            parameters["locked"]!.ToObject<bool>() == true)
        {
            doc.Objects.Show(id, false);
            doc.Objects.Lock(id, false);
        }

        doc.Views.Redraw();

        var updated = doc.Objects.Find(id);
        if (updated == null)
            throw new InvalidOperationException($"Object with id {id} not found after update.");

        return SerializeObjectAttributes(updated);
    }

    private bool HasObjectAttributeUpdates(JObject parameters)
    {
        string[] updateKeys =
        {
            "new_name",
            "layer",
            "color",
            "material_index",
            "visible",
            "locked",
            "user_strings",
            "delete_user_strings",
            "clear_user_strings"
        };
        return updateKeys.Any(parameters.ContainsKey);
    }

    private JObject SerializeObjectAttributes(RhinoObject obj)
    {
        var doc = obj.Document ?? RhinoDoc.ActiveDoc;
        var attrs = obj.Attributes;
        var layer = doc.Layers[attrs.LayerIndex];

        return new JObject
        {
            ["id"] = obj.Id.ToString(),
            ["name"] = obj.Name ?? string.Empty,
            ["type"] = GetNormalizedType(obj),
            ["layer"] = new JObject
            {
                ["index"] = layer.Index,
                ["id"] = layer.Id.ToString(),
                ["name"] = layer.Name,
                ["full_path"] = layer.FullPath
            },
            ["color"] = Serializer.SerializeColor(attrs.ObjectColor),
            ["color_source"] = attrs.ColorSource.ToString(),
            ["material_index"] = attrs.MaterialIndex,
            ["material_source"] = attrs.MaterialSource.ToString(),
            ["visible"] = obj.Visible,
            ["locked"] = obj.IsLocked,
            ["hidden"] = obj.IsHidden,
            ["normal"] = obj.IsNormal,
            ["user_strings"] = Serializer.RhinoObjectAttributes(obj)
        };
    }

    private Layer FindLayerByNameOrFullPath(RhinoDoc doc, string nameOrFullPath)
    {
        var layer = doc.Layers.FindName(nameOrFullPath);
        if (layer != null && !layer.IsDeleted) return layer;

        return doc.Layers.FirstOrDefault(layerCandidate =>
            !layerCandidate.IsDeleted &&
            layerCandidate.FullPath.Equals(nameOrFullPath, StringComparison.OrdinalIgnoreCase));
    }
}
