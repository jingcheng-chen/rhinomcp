using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoMCP.Shared.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Modifies an existing object in the Rhino document.
    /// </summary>
    /// <param name="parameters">
    /// JSON object containing:
    /// - id: GUID of the object to modify (required if name not provided)
    /// - name: Name of the object to modify (required if id not provided)
    /// - new_name: Optional new name for the object
    /// - new_color: Optional [r, g, b] color array (0-255)
    /// - translation: Optional [x, y, z] translation vector
    /// - rotation: Optional [x, y, z] rotation in radians (applied around object center)
    /// - scale: Optional [x, y, z] scale factors (applied from bounding box min)
    /// </param>
    /// <returns>JSON object with updated object info</returns>
    /// <exception cref="InvalidOperationException">Thrown when object is not found</exception>
    public JObject ModifyObject(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var obj = getObjectByIdOrName(parameters);
        var geometry = obj.Geometry;
        var xform = Transform.Identity;

        // Handle different modifications based on parameters
        bool attributesModified = false;
        bool geometryModified = false;

        // Change name if provided
        if (parameters["new_name"] != null)
        {
            string name = parameters["new_name"].ToString();
            obj.Attributes.Name = name;
            attributesModified = true;
        }

        // Change color if provided
        if (parameters["new_color"] != null)
        {
            int[] color = parameters["new_color"]?.ToObject<int[]>() ?? new[] { 0, 0, 0 };
            obj.Attributes.ObjectColor = Color.FromArgb(color[0], color[1], color[2]);
            obj.Attributes.ColorSource = ObjectColorSource.ColorFromObject;
            attributesModified = true;
        }

        // Change translation if provided
        if (parameters["translation"] != null)
        {
            xform *= applyTranslation(parameters);
            geometryModified = true;
        }

        // Apply scale if provided
        if (parameters["scale"] != null)
        {
            xform *= applyScale(parameters, geometry);
            geometryModified = true;
        }

        // Apply rotation if provided
        if (parameters["rotation"] != null)
        {
            xform *= applyRotation(parameters, geometry);
            geometryModified = true;
        }

        if (attributesModified)
        {
            // Update the object attributes if needed
            doc.Objects.ModifyAttributes(obj, obj.Attributes, true);
        }

        if (geometryModified)
        {
            // Update the object geometry if needed
            doc.Objects.Transform(obj, xform, true);
        }

        // Update views
        doc.Views.Redraw();

        return Serializer.RhinoObject(getObjectByIdOrName(new JObject { ["id"] = obj.Id }));

    }
}