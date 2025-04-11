using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
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
            int[] color = parameters["new_color"]?.ToObject<int[]>() ?? new [] { 0, 0, 0 };
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

        return GetObjectInfo(new JObject { ["id"] = obj.Id });
    }
}