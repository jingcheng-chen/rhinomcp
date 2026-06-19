using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Partial class containing utility methods for RhinoMCP functions.
/// Provides JSON parsing helpers and transformation utilities.
/// </summary>
public partial class RhinoMCPFunctions
{
    /// <summary>Casts a JSON token to double, defaulting to 0 if null.</summary>
    private double castToDouble(JToken token)
    {
        return token?.ToObject<double>() ?? 0;
    }
    private double[] castToDoubleArray(JToken token)
    {
        return token?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
    }
    private double[][] castToDoubleArray2D(JToken token)
    {
        List<double[]> result = new List<double[]>();
        foreach (var t in (JArray)token)
        {
            double[] inner = castToDoubleArray(t);
            result.Add(inner);
        }
        return result.ToArray();
    }
    private int castToInt(JToken token)
    {
        return token?.ToObject<int>() ?? 0;
    }
    private int[] castToIntArray(JToken token)
    {
        return token?.ToObject<int[]>() ?? new int[] { 0, 0, 0 };
    }

    private bool[] castToBoolArray(JToken token)
    {
        return token?.ToObject<bool[]>() ?? new bool[] { false, false };
    }

    private List<string> castToStringList(JToken token)
    {
        return token?.ToObject<List<string>>() ?? new List<string>();
    }

    private bool castToBool(JToken token)
    {
        return token?.ToObject<bool>() ?? false;
    }

    private string castToString(JToken token)
    {
        return token?.ToString() ?? string.Empty;
    }

    private Guid castToGuid(JToken token)
    {
        var guid = token?.ToString();
        if (guid == null) return Guid.Empty;
        return new Guid(guid);
    }

    private List<Point3d> castToPoint3dList(JToken token)
    {
        double[][] points = castToDoubleArray2D(token);
        var ptList = new List<Point3d>();
        foreach (var point in points)
        {
            ptList.Add(new Point3d(point[0], point[1], point[2]));
        }
        return ptList;
    }

    private Point3d castToPoint3d(JToken token)
    {
        double[] point = castToDoubleArray(token);
        return new Point3d(point[0], point[1], point[2]);
    }

    private RhinoObject getObjectByIdOrName(JObject parameters)
    {
        string objectId = parameters["id"]?.ToString();
        string objectName = parameters["name"]?.ToString();

        var doc = RhinoDoc.ActiveDoc;

        if (!string.IsNullOrEmpty(objectId))
        {
            if (!Guid.TryParse(objectId, out var guid))
                throw new InvalidOperationException($"Invalid GUID '{objectId}'.");
            var obj = doc.Objects.Find(guid);
            if (obj == null)
                throw new InvalidOperationException($"Object with id {objectId} not found.");
            return obj;
        }

        if (!string.IsNullOrEmpty(objectName))
        {
            var objs = doc.Objects.GetObjectList(new ObjectEnumeratorSettings { NameFilter = objectName }).ToList();
            if (objs.Count == 0)
                throw new InvalidOperationException($"Object with name '{objectName}' not found.");
            if (objs.Count > 1)
                throw new InvalidOperationException($"Multiple objects with name '{objectName}' found.");
            return objs[0];
        }

        throw new InvalidOperationException("Object lookup requires 'id' or 'name'.");
    }

    /// <summary>
    /// Count the active (non-deleted) objects in the document. This walks the
    /// same object enumeration get_document_summary categorizes, so the count
    /// always agrees with that breakdown. RhinoObjectTable.Count is deliberately
    /// not used: it also counts objects that were deleted but are still undoable,
    /// so it over-reports until the undo history is cleared.
    /// </summary>
    private int CountActiveObjects(RhinoDoc doc)
    {
        int count = 0;
        foreach (var obj in doc.Objects) count++;
        return count;
    }

    private Transform applyRotation(JObject parameters, GeometryBase geometry)
    {
        double[] rotation = parameters["rotation"].ToObject<double[]>();
        var xform = Transform.Identity;

        // Calculate the center for rotation
        BoundingBox bbox = geometry.GetBoundingBox(true);
        Point3d center = bbox.Center;

        // Create rotation transformations (in radians)
        Transform rotX = Transform.Rotation(rotation[0], Vector3d.XAxis, center);
        Transform rotY = Transform.Rotation(rotation[1], Vector3d.YAxis, center);
        Transform rotZ = Transform.Rotation(rotation[2], Vector3d.ZAxis, center);

        // Apply transformations
        xform *= rotX;
        xform *= rotY;
        xform *= rotZ;

        return xform;
    }

    private Transform applyTranslation(JObject parameters)
    {
        double[] translation = parameters["translation"].ToObject<double[]>();
        var xform = Transform.Identity;
        Vector3d move = new Vector3d(translation[0], translation[1], translation[2]);
        xform *= Transform.Translation(move);

        return xform;
    }

    private Transform applyScale(JObject parameters, GeometryBase geometry)
    {
        double[] scale = parameters["scale"].ToObject<double[]>();
        var xform = Transform.Identity;

        // Calculate the min for scaling
        BoundingBox bbox = geometry.GetBoundingBox(true);
        Point3d anchor = bbox.Min;
        Plane plane = Plane.WorldXY;
        plane.Origin = anchor;

        // Create scale transformation
        Transform scaleTransform = Transform.Scale(plane, scale[0], scale[1], scale[2]);
        xform *= scaleTransform;

        return xform;
    }
}