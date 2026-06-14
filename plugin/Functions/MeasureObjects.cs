using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Reports the spatial relationship between two objects: whether they clash
    /// (intersect) and the gap between their bounding boxes. Read-only.
    ///
    /// clash is exact for the cases RhinoCommon gives an exact pairwise
    /// intersection for (brep/brep, curve/curve), and for two closed solids it
    /// also reports a clash when one is fully contained in the other (their
    /// surfaces never cross in that case); for anything else it falls
    /// back to bounding-box overlap, and the `method` field always says which
    /// was used so the caller knows how precise the answer is. bbox_gap is the
    /// exact minimum distance between the two axis-aligned bounding boxes (0 if
    /// they meet or overlap), which is a conservative lower bound on the true
    /// surface-to-surface distance. It is emitted as a raw number, not through
    /// the point serializer, so it is not rounded.
    /// </summary>
    [McpCommand("measure_objects", ReadOnly = true)]
    public JObject MeasureObjects(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var ids = parameters["object_ids"]?.ToObject<List<string>>() ?? new List<string>();
        if (ids.Count != 2)
            throw new ArgumentException("measure_objects requires object_ids with exactly two object ids.");

        var objA = getObjectByIdOrName(new JObject { ["id"] = ids[0] });
        var objB = getObjectByIdOrName(new JObject { ["id"] = ids[1] });

        var geoA = objA.Geometry;
        var geoB = objB.Geometry;
        double tol = doc.ModelAbsoluteTolerance;

        var bboxA = geoA.GetBoundingBox(true);
        var bboxB = geoB.GetBoundingBox(true);
        double bboxGap = BoundingBoxGap(bboxA, bboxB);

        var brepA = TryGetBrep(geoA);
        var brepB = TryGetBrep(geoB);
        var curveA = geoA as Curve;
        var curveB = geoB as Curve;

        bool clash;
        int intersectionCount;
        string method;

        if (brepA != null && brepB != null)
        {
            Rhino.Geometry.Intersect.Intersection.BrepBrep(
                brepA, brepB, tol, out Curve[] curves, out Point3d[] points);
            int nc = curves?.Length ?? 0;
            int np = points?.Length ?? 0;
            intersectionCount = nc + np;
            clash = intersectionCount > 0;
            // Surfaces that don't cross can still clash when one solid sits fully
            // inside the other: their surfaces never intersect in that case. For
            // two closed solids, fall back to a containment test.
            if (!clash && brepA.IsSolid && brepB.IsSolid)
                clash = BrepContains(brepA, brepB, tol) || BrepContains(brepB, brepA, tol);
            method = "brep";
        }
        else if (curveA != null && curveB != null)
        {
            var events = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveA, curveB, tol, tol);
            intersectionCount = events?.Count ?? 0;
            clash = intersectionCount > 0;
            method = "curve";
        }
        else
        {
            // No exact pairwise intersection available for this pair (points,
            // meshes, or mixed curve/brep): report bounding-box overlap, and
            // say so via method so the caller doesn't read it as exact.
            clash = bboxGap <= tol;
            intersectionCount = 0;
            method = "bbox";
        }

        return new JObject
        {
            ["object_a"] = objA.Id.ToString(),
            ["object_b"] = objB.Id.ToString(),
            ["clash"] = clash,
            ["intersection_count"] = intersectionCount,
            ["bbox_gap"] = bboxGap,
            ["method"] = method
        };
    }

    /// <summary>Brep for the geometry where one is available, else null.</summary>
    private Brep TryGetBrep(GeometryBase geometry)
    {
        if (geometry is Brep brep) return brep;
        if (geometry is Extrusion extrusion) return extrusion.ToBrep();
        if (geometry is Surface surface) return surface.ToBrep();
        return null;
    }

    /// <summary>
    /// True when the closed solid <paramref name="outer"/> contains
    /// <paramref name="inner"/>. Tests a vertex of inner, which lies on inner's
    /// surface; if that point is inside outer and the two surfaces do not cross,
    /// inner sits entirely within outer. Caller guards that both breps are solid,
    /// which IsPointInside requires.
    /// </summary>
    private bool BrepContains(Brep outer, Brep inner, double tol)
    {
        var vertices = inner.Vertices;
        if (vertices == null || vertices.Count == 0) return false;
        return outer.IsPointInside(vertices[0].Location, tol, false);
    }

    /// <summary>
    /// Exact minimum Euclidean distance between two axis-aligned bounding boxes,
    /// 0 when they meet or overlap. Per axis the gap is the positive separation
    /// (or 0 if they overlap on that axis); the total is their root-sum-square.
    /// </summary>
    private double BoundingBoxGap(BoundingBox a, BoundingBox b)
    {
        double gx = Math.Max(0, Math.Max(a.Min.X - b.Max.X, b.Min.X - a.Max.X));
        double gy = Math.Max(0, Math.Max(a.Min.Y - b.Max.Y, b.Min.Y - a.Max.Y));
        double gz = Math.Max(0, Math.Max(a.Min.Z - b.Max.Z, b.Min.Z - a.Max.Z));
        return Math.Sqrt(gx * gx + gy * gy + gz * gz);
    }
}
