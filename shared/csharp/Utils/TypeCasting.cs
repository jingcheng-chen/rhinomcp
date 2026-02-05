using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace RhinoMCP.Shared.Utils;

/// <summary>
/// Utility methods for casting JSON tokens to typed values.
/// Used by both RhinoMCP and GrasshopperMCP plugins.
/// </summary>
public static class TypeCasting
{
    /// <summary>Casts a JSON token to double, defaulting to 0 if null.</summary>
    public static double ToDouble(JToken? token)
    {
        return token?.ToObject<double>() ?? 0;
    }

    /// <summary>Casts a JSON token to double array, defaulting to [0,0,0] if null.</summary>
    public static double[] ToDoubleArray(JToken? token)
    {
        return token?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
    }

    /// <summary>Casts a JSON token to 2D double array.</summary>
    public static double[][] ToDoubleArray2D(JToken? token)
    {
        if (token == null) return Array.Empty<double[]>();

        List<double[]> result = new List<double[]>();
        foreach (var t in (JArray)token)
        {
            double[] inner = ToDoubleArray(t);
            result.Add(inner);
        }
        return result.ToArray();
    }

    /// <summary>Casts a JSON token to int, defaulting to 0 if null.</summary>
    public static int ToInt(JToken? token)
    {
        return token?.ToObject<int>() ?? 0;
    }

    /// <summary>Casts a JSON token to int array, defaulting to [0,0,0] if null.</summary>
    public static int[] ToIntArray(JToken? token)
    {
        return token?.ToObject<int[]>() ?? new int[] { 0, 0, 0 };
    }

    /// <summary>Casts a JSON token to bool array, defaulting to [false, false] if null.</summary>
    public static bool[] ToBoolArray(JToken? token)
    {
        return token?.ToObject<bool[]>() ?? new bool[] { false, false };
    }

    /// <summary>Casts a JSON token to string list, defaulting to empty list if null.</summary>
    public static List<string> ToStringList(JToken? token)
    {
        return token?.ToObject<List<string>>() ?? new List<string>();
    }

    /// <summary>Casts a JSON token to bool, defaulting to false if null.</summary>
    public static bool ToBool(JToken? token)
    {
        return token?.ToObject<bool>() ?? false;
    }

    /// <summary>Casts a JSON token to string, defaulting to empty string if null.</summary>
    public static string ToString(JToken? token)
    {
        return token?.ToString() ?? string.Empty;
    }

    /// <summary>Casts a JSON token to Guid, defaulting to Guid.Empty if null.</summary>
    public static Guid ToGuid(JToken? token)
    {
        var guid = token?.ToString();
        if (guid == null) return Guid.Empty;
        return new Guid(guid);
    }

    /// <summary>Casts a JSON token to Point3d.</summary>
    public static Point3d ToPoint3d(JToken? token)
    {
        double[] point = ToDoubleArray(token);
        return new Point3d(point[0], point[1], point[2]);
    }

    /// <summary>Casts a JSON token to List of Point3d.</summary>
    public static List<Point3d> ToPoint3dList(JToken? token)
    {
        double[][] points = ToDoubleArray2D(token);
        var ptList = new List<Point3d>();
        foreach (var point in points)
        {
            ptList.Add(new Point3d(point[0], point[1], point[2]));
        }
        return ptList;
    }

    /// <summary>Casts a JSON token to Vector3d.</summary>
    public static Vector3d ToVector3d(JToken? token)
    {
        double[] vec = ToDoubleArray(token);
        return new Vector3d(vec[0], vec[1], vec[2]);
    }

    /// <summary>Casts a JSON token to Plane (from origin and optional normal).</summary>
    public static Plane ToPlane(JToken? originToken, JToken? normalToken = null)
    {
        var origin = ToPoint3d(originToken);
        if (normalToken != null)
        {
            var normal = ToVector3d(normalToken);
            return new Plane(origin, normal);
        }
        return new Plane(origin, Vector3d.ZAxis);
    }
}
