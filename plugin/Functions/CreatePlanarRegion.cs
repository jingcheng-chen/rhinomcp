using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Geometry.Intersect;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Creates exactly one open planar Brep face from validated boundary curves.
    /// Input document objects are never modified or deleted.
    /// </summary>
    [McpCommand("create_planar_region")]
    public JObject CreatePlanarRegion(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var tolerance = doc.ModelAbsoluteTolerance;
        var outerText = parameters["outer_curve_id"]?.ToString();
        var innerTexts = parameters["inner_curve_ids"]?.ToObject<List<string>>()
            ?? new List<string>();
        var name = parameters["name"]?.ToString();

        if (!Guid.TryParse(outerText, out var outerId))
            throw new ArgumentException("create_planar_region requires a valid outer_curve_id GUID");

        var ids = new List<Guid> { outerId };
        foreach (var text in innerTexts)
        {
            if (!Guid.TryParse(text, out var id))
                throw new ArgumentException($"Invalid inner curve GUID '{text}'");
            ids.Add(id);
        }

        if (ids.Distinct().Count() != ids.Count)
            throw new ArgumentException("Outer and inner curve IDs must all be distinct");

        var curves = new List<Curve>();
        Brep[] planarBreps = null;
        try
        {
            for (var index = 0; index < ids.Count; index++)
            {
                var role = index == 0 ? "outer" : $"inner {index}";
                var obj = doc.Objects.Find(ids[index]);
                if (obj == null)
                    throw new InvalidOperationException($"{role} curve object {ids[index]} was not found");
                if (obj.Geometry is not Curve source)
                    throw new InvalidOperationException($"Object {ids[index]} is not a curve");

                var curve = source.DuplicateCurve();
                if (curve == null)
                    throw new InvalidOperationException($"Could not duplicate {role} curve {ids[index]}");
                curves.Add(curve);

                if (!curve.IsValid)
                    throw new InvalidOperationException($"{role} curve {ids[index]} has invalid geometry");
                if (!curve.IsClosed)
                    throw new InvalidOperationException($"{role} curve {ids[index]} must be closed");
                if (!curve.TryGetPlane(out _, tolerance))
                    throw new InvalidOperationException($"{role} curve {ids[index]} must be planar");
                var selfEvents = Intersection.CurveSelf(curve, tolerance);
                if (selfEvents != null && selfEvents.Count > 0)
                    throw new InvalidOperationException($"{role} curve {ids[index]} self-intersects");
            }

            var outer = curves[0];
            if (!outer.TryGetPlane(out var plane, tolerance))
                throw new InvalidOperationException("Outer curve must define a plane");

            for (var index = 1; index < curves.Count; index++)
            {
                if (!curves[index].IsInPlane(plane, tolerance))
                {
                    throw new InvalidOperationException(
                        $"Inner curve {innerTexts[index - 1]} is not coplanar with the outer curve");
                }

                var boundaryEvents = Intersection.CurveCurve(
                    curves[index], outer, tolerance, tolerance);
                if (boundaryEvents != null && boundaryEvents.Count > 0)
                    throw new InvalidOperationException(
                        $"Inner curve {innerTexts[index - 1]} crosses or touches the outer curve");

                var relation = Curve.PlanarClosedCurveRelationship(
                    curves[index], outer, plane, tolerance);
                if (relation != RegionContainment.AInsideB)
                    throw new InvalidOperationException(
                        $"Inner curve {innerTexts[index - 1]} must be strictly inside the outer curve");
            }

            for (var first = 1; first < curves.Count; first++)
            {
                for (var second = first + 1; second < curves.Count; second++)
                {
                    var events = Intersection.CurveCurve(
                        curves[first], curves[second], tolerance, tolerance);
                    if (events != null && events.Count > 0)
                        throw new InvalidOperationException(
                            "Inner curves must not cross or touch each other");

                    var relation = Curve.PlanarClosedCurveRelationship(
                        curves[first], curves[second], plane, tolerance);
                    if (relation != RegionContainment.Disjoint)
                        throw new InvalidOperationException(
                            "Inner curves must be pairwise disjoint and nonnested");
                }
            }

            planarBreps = Brep.CreatePlanarBreps(curves, tolerance);
            if (planarBreps == null || planarBreps.Length != 1)
                throw new InvalidOperationException(
                    "Planar-region construction did not produce exactly one Brep");

            var result = planarBreps[0];
            var outerLoops = result.Loops.Count(loop => loop.LoopType == BrepLoopType.Outer);
            var innerLoops = result.Loops.Count(loop => loop.LoopType == BrepLoopType.Inner);
            if (!result.IsValid || result.IsSolid || result.Faces.Count != 1
                || !result.Faces[0].IsPlanar(tolerance)
                || outerLoops != 1 || innerLoops != innerTexts.Count
                || result.Loops.Count != innerTexts.Count + 1)
            {
                throw new InvalidOperationException(
                    "Planar-region construction produced invalid or unexpected topology");
            }

            var attributes = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attributes.Name = name;
            var resultId = doc.Objects.AddBrep(result, attributes);
            if (resultId == Guid.Empty)
                throw new InvalidOperationException("Failed to add the planar region to the document");

            doc.Views.Redraw();
            return new JObject
            {
                ["success"] = true,
                ["id"] = resultId.ToString(),
                ["face_count"] = result.Faces.Count,
                ["loop_count"] = result.Loops.Count,
                ["outer_loop_count"] = outerLoops,
                ["inner_loop_count"] = innerLoops,
                ["message"] = $"Created one planar Brep face with {innerLoops} inner loop(s)"
            };
        }
        finally
        {
            if (planarBreps != null)
            {
                foreach (var brep in planarBreps)
                    brep?.Dispose();
            }
            foreach (var curve in curves)
                curve.Dispose();
        }
    }
}
