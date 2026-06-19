using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Cuts a plane through the selected objects and reports each resulting
    /// cross-section's area, perimeter, and centroid. Nothing is added to the
    /// document: the contour curves are produced in memory, measured, and
    /// discarded, so the command is read-only.
    ///
    /// Two modes (exactly one required):
    ///   plane   - one cut. {axis, value} for an axis-aligned world plane, or
    ///             {origin, normal} for an arbitrary plane. Returns per-object
    ///             section profiles (loops with area/perimeter/centroid).
    ///   profile - a stack of `count` parallel cuts along an axis, spanning the
    ///             selection's extent (or an explicit start/end). Returns the
    ///             sectional-area curve: one total area + loop count per slice.
    ///
    /// Honesty rules: a single cut can yield several disjoint loops (a tube, a
    /// torus, the two legs of an L), so loop areas are summed per object. An area
    /// is reported only for a loop that closed AND is planar; an open or
    /// non-planar section is marked closed:false with a perimeter and no
    /// fabricated area. Perimeter is the loop's curve length (AreaMassProperties
    /// has no perimeter).
    /// </summary>
    [McpCommand("section_profile", ReadOnly = true)]
    public JObject SectionProfile(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        double tol = doc.ModelAbsoluteTolerance;
        var targets = ResolveAnalysisTargets(parameters);

        bool hasPlane = parameters["plane"] is JObject;
        bool hasProfile = parameters["profile"] is JObject;
        if (hasPlane == hasProfile)
            throw new ArgumentException("section_profile requires exactly one of 'plane' or 'profile'.");

        if (hasPlane)
            return SectionAtSinglePlane(tol, targets, (JObject)parameters["plane"]);
        return SectionProfileStack(tol, targets, (JObject)parameters["profile"]);
    }

    private JObject SectionAtSinglePlane(double tol, List<RhinoObject> targets, JObject planeSpec)
    {
        Plane plane = ParseSectionPlane(planeSpec);

        var profiles = new JArray();
        double totalArea = 0.0;
        int totalLoops = 0;

        foreach (var obj in targets)
        {
            (JArray loops, double objArea, int loopCount) = SectionObject(obj, plane, tol);
            totalArea += objArea;
            totalLoops += loopCount;
            profiles.Add(new JObject
            {
                ["id"] = obj.Id.ToString(),
                ["name"] = obj.Name ?? "(unnamed)",
                ["type"] = GetNormalizedType(obj),
                ["section_area"] = objArea,
                ["loop_count"] = loopCount,
                ["loops"] = loops
            });
        }

        return new JObject
        {
            ["mode"] = "plane",
            ["object_count"] = targets.Count,
            ["plane"] = SerializePlane(plane),
            ["total_section_area"] = totalArea,
            ["total_loop_count"] = totalLoops,
            ["profiles"] = profiles
        };
    }

    private JObject SectionProfileStack(double tol, List<RhinoObject> targets, JObject profileSpec)
    {
        string axis = (profileSpec["axis"]?.ToString() ?? string.Empty).ToUpperInvariant();
        AxisToNormal(axis); // validates axis early

        int count = profileSpec["count"]?.ToObject<int>() ?? 0;
        if (count < 2)
            throw new ArgumentException("section_profile profile.count must be at least 2.");
        if (count > 100)
            throw new ArgumentException("section_profile profile.count must be at most 100.");

        // Span along the axis: explicit start/end win; otherwise the combined
        // bounding box of the selection along that axis.
        bool hasStart = profileSpec["start"] != null;
        bool hasEnd = profileSpec["end"] != null;

        double lo, hi;
        if (hasStart && hasEnd)
        {
            lo = profileSpec["start"].ToObject<double>();
            hi = profileSpec["end"].ToObject<double>();
        }
        else
        {
            BoundingBox combined = BoundingBox.Empty;
            foreach (var obj in targets)
            {
                var b = obj.Geometry.GetBoundingBox(true);
                if (!b.IsValid) continue;
                combined = combined.IsValid ? BoundingBox.Union(combined, b) : b;
            }
            if (!combined.IsValid)
                throw new InvalidOperationException("Cannot derive a profile span: the selection has no valid bounding box.");

            (double bmin, double bmax) = AxisExtent(combined, axis);
            lo = hasStart ? profileSpec["start"].ToObject<double>() : bmin;
            hi = hasEnd ? profileSpec["end"].ToObject<double>() : bmax;
        }
        if (hi < lo) { (lo, hi) = (hi, lo); }

        double span = hi - lo;
        var sections = new JArray();
        for (int i = 0; i < count; i++)
        {
            // Sample at the midpoint of each of `count` equal bins so the end
            // planes don't graze the extreme faces of the selection.
            double position = lo + span * (i + 0.5) / count;
            Plane plane = PlaneAt(axis, position);

            double sliceArea = 0.0;
            int sliceLoops = 0;
            foreach (var obj in targets)
            {
                (JArray _, double objArea, int loopCount) = SectionObject(obj, plane, tol);
                sliceArea += objArea;
                sliceLoops += loopCount;
            }
            sections.Add(new JObject
            {
                ["position"] = position,
                ["total_section_area"] = sliceArea,
                ["loop_count"] = sliceLoops
            });
        }

        return new JObject
        {
            ["mode"] = "profile",
            ["object_count"] = targets.Count,
            ["axis"] = axis,
            ["count"] = count,
            ["sections"] = sections
        };
    }

    /// <summary>
    /// Section one object with one plane. Returns the per-loop report, the summed
    /// closed-loop area, and the loop count. A type with no surface to cut
    /// (points, curves) or a plane that misses the object yields no loops.
    /// </summary>
    private (JArray loops, double area, int loopCount) SectionObject(RhinoObject obj, Plane plane, double tol)
    {
        var loops = new JArray();
        double area = 0.0;

        Curve[] fragments = null;
        var geo = obj.Geometry;
        if (geo is Mesh mesh)
        {
            // The (Mesh, Plane) overload is deprecated; the tolerance overload
            // wants an intersection tolerance near 1e-7 (McNeel guidance), not
            // the coarser model tolerance.
            fragments = Mesh.CreateContourCurves(mesh, plane, RhinoMath.SqrtEpsilon * 10.0);
        }
        else
        {
            var brep = GetBrepFromObject(obj);
            if (brep != null)
                fragments = Brep.CreateContourCurves(brep, plane);
        }

        if (fragments == null || fragments.Length == 0)
            return (loops, 0.0, 0);

        // CreateContourCurves returns fragments; join them into whole loops at the
        // model tolerance. Brep contouring has no tolerance overload, so the join
        // tolerance is what decides whether a section reads as closed.
        Curve[] joined = Curve.JoinCurves(fragments, tol);
        if (joined == null || joined.Length == 0)
            joined = fragments;

        foreach (var curve in joined)
        {
            if (curve == null) continue;

            bool closed = curve.IsClosed && curve.IsPlanar(tol);
            var loop = new JObject
            {
                ["closed"] = closed,
                ["perimeter"] = curve.GetLength(),
                ["area"] = null,
                ["centroid"] = null
            };

            if (closed)
            {
                var amp = AreaMassProperties.Compute(curve);
                if (amp != null)
                {
                    loop["area"] = amp.Area;
                    loop["centroid"] = Serializer.SerializePoint(amp.Centroid);
                    area += amp.Area;
                }
            }

            loops.Add(loop);
        }

        return (loops, area, joined.Length);
    }

    private Plane ParseSectionPlane(JObject spec)
    {
        bool hasAxis = spec["axis"] != null || spec["value"] != null;
        bool hasOriginNormal = spec["origin"] != null || spec["normal"] != null;
        if (hasAxis && hasOriginNormal)
            throw new ArgumentException("section_profile plane takes either {axis, value} or {origin, normal}, not both.");

        if (spec["axis"] != null && spec["value"] != null)
        {
            string axis = spec["axis"].ToString().ToUpperInvariant();
            double value = spec["value"].ToObject<double>();
            return PlaneAt(axis, value);
        }

        if (spec["origin"] != null && spec["normal"] != null)
        {
            Point3d origin = castToPoint3d(spec["origin"]);
            double[] n = spec["normal"].ToObject<double[]>();
            if (n == null || n.Length != 3)
                throw new ArgumentException("section_profile plane normal must be [x, y, z].");
            var normal = new Vector3d(n[0], n[1], n[2]);
            if (!normal.Unitize())
                throw new ArgumentException("section_profile plane normal must be a non-zero vector.");
            var plane = new Plane(origin, normal);
            if (!plane.IsValid)
                throw new ArgumentException("section_profile plane is invalid.");
            return plane;
        }

        throw new ArgumentException("section_profile plane requires {axis, value} or {origin, normal}.");
    }

    private Vector3d AxisToNormal(string axis)
    {
        switch (axis)
        {
            case "X": return Vector3d.XAxis;
            case "Y": return Vector3d.YAxis;
            case "Z": return Vector3d.ZAxis;
            default: throw new ArgumentException("section_profile axis must be 'X', 'Y', or 'Z'.");
        }
    }

    private Plane PlaneAt(string axis, double value)
    {
        Vector3d normal = AxisToNormal(axis);
        var origin = new Point3d(normal.X * value, normal.Y * value, normal.Z * value);
        return new Plane(origin, normal);
    }

    private (double min, double max) AxisExtent(BoundingBox bbox, string axis)
    {
        switch (axis)
        {
            case "X": return (bbox.Min.X, bbox.Max.X);
            case "Y": return (bbox.Min.Y, bbox.Max.Y);
            case "Z": return (bbox.Min.Z, bbox.Max.Z);
            default: throw new ArgumentException("section_profile axis must be 'X', 'Y', or 'Z'.");
        }
    }

    private JObject SerializePlane(Plane plane)
    {
        var n = plane.Normal;
        return new JObject
        {
            ["origin"] = Serializer.SerializePoint(plane.Origin),
            ["normal"] = new JArray { Math.Round(n.X, 6), Math.Round(n.Y, 6), Math.Round(n.Z, 6) }
        };
    }
}
