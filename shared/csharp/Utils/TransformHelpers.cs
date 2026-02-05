using System;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace RhinoMCP.Shared.Utils;

/// <summary>
/// Utility methods for creating geometric transformations from JSON parameters.
/// Used by both RhinoMCP and GrasshopperMCP plugins.
/// </summary>
public static class TransformHelpers
{
    /// <summary>
    /// Create a rotation transform from JSON parameters.
    /// Rotates around the geometry's bounding box center.
    /// </summary>
    /// <param name="parameters">JSON object containing "rotation" as [rx, ry, rz] in radians</param>
    /// <param name="geometry">The geometry to rotate (used to find center point)</param>
    /// <returns>Combined rotation transform</returns>
    public static Transform CreateRotation(JObject parameters, GeometryBase geometry)
    {
        var rotationToken = parameters["rotation"];
        if (rotationToken == null) return Transform.Identity;

        double[] rotation = rotationToken.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
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

    /// <summary>
    /// Create a translation transform from JSON parameters.
    /// </summary>
    /// <param name="parameters">JSON object containing "translation" as [tx, ty, tz]</param>
    /// <returns>Translation transform</returns>
    public static Transform CreateTranslation(JObject parameters)
    {
        var translationToken = parameters["translation"];
        if (translationToken == null) return Transform.Identity;

        double[] translation = translationToken.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
        Vector3d move = new Vector3d(translation[0], translation[1], translation[2]);
        return Transform.Translation(move);
    }

    /// <summary>
    /// Create a scale transform from JSON parameters.
    /// Scales from the geometry's bounding box minimum point.
    /// </summary>
    /// <param name="parameters">JSON object containing "scale" as [sx, sy, sz]</param>
    /// <param name="geometry">The geometry to scale (used to find anchor point)</param>
    /// <returns>Scale transform</returns>
    public static Transform CreateScale(JObject parameters, GeometryBase geometry)
    {
        var scaleToken = parameters["scale"];
        if (scaleToken == null) return Transform.Identity;

        double[] scale = scaleToken.ToObject<double[]>() ?? new double[] { 1, 1, 1 };

        // Calculate the min for scaling
        BoundingBox bbox = geometry.GetBoundingBox(true);
        Point3d anchor = bbox.Min;
        Plane plane = Plane.WorldXY;
        plane.Origin = anchor;

        // Create scale transformation
        return Transform.Scale(plane, scale[0], scale[1], scale[2]);
    }

    /// <summary>
    /// Create a combined transform from all available parameters (translation, rotation, scale).
    /// Order: Scale -> Rotate -> Translate
    /// </summary>
    /// <param name="parameters">JSON object potentially containing translation, rotation, and scale</param>
    /// <param name="geometry">The geometry being transformed</param>
    /// <returns>Combined transform</returns>
    public static Transform CreateCombinedTransform(JObject parameters, GeometryBase geometry)
    {
        var xform = Transform.Identity;

        // Apply in order: Scale, Rotate, Translate
        if (parameters["scale"] != null)
        {
            xform *= CreateScale(parameters, geometry);
        }

        if (parameters["rotation"] != null)
        {
            xform *= CreateRotation(parameters, geometry);
        }

        if (parameters["translation"] != null)
        {
            xform *= CreateTranslation(parameters);
        }

        return xform;
    }

    /// <summary>
    /// Create a uniform scale transform.
    /// </summary>
    /// <param name="factor">Scale factor</param>
    /// <param name="center">Center point for scaling</param>
    /// <returns>Uniform scale transform</returns>
    public static Transform CreateUniformScale(double factor, Point3d center)
    {
        return Transform.Scale(center, factor);
    }

    /// <summary>
    /// Create a mirror transform across a plane.
    /// </summary>
    /// <param name="mirrorPlane">Plane to mirror across</param>
    /// <returns>Mirror transform</returns>
    public static Transform CreateMirror(Plane mirrorPlane)
    {
        return Transform.Mirror(mirrorPlane);
    }
}
