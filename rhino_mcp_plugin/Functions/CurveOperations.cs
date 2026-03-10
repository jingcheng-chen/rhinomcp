using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Geometry.Intersect;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Curve operations: Project, Intersect, Split
/// </summary>
public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Project a curve onto surfaces or polysurfaces.
    /// </summary>
    public JObject ProjectCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveId = parameters["curve_id"]?.ToString();
        var targetIds = parameters["target_ids"]?.ToObject<List<string>>();
        var direction = parameters["direction"]?.ToObject<List<double>>();
        var name = parameters["name"]?.ToString();

        if (string.IsNullOrEmpty(curveId))
            throw new ArgumentException("Project requires a curve_id");

        if (targetIds == null || targetIds.Count == 0)
            throw new ArgumentException("Project requires at least one target surface/polysurface ID");

        if (direction == null || direction.Count != 3)
            throw new ArgumentException("Project requires a direction vector [x, y, z]");

        var curveObj = doc.Objects.Find(new Guid(curveId));
        if (curveObj == null)
            throw new InvalidOperationException($"Curve object with ID {curveId} not found");

        var curve = curveObj.Geometry as Curve;
        if (curve == null)
            throw new InvalidOperationException($"Object {curveId} is not a curve");

        var directionVec = new Vector3d(direction[0], direction[1], direction[2]);
        var breps = new List<Brep>();
        var meshes = new List<Mesh>();

        foreach (var idStr in targetIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null) continue;

            if (obj.Geometry is Brep brep)
                breps.Add(brep);
            else if (obj.Geometry is Mesh mesh)
                meshes.Add(mesh);
            else if (obj.Geometry is Extrusion extrusion)
                breps.Add(extrusion.ToBrep());
        }

        if (breps.Count == 0 && meshes.Count == 0)
            throw new InvalidOperationException("No valid target surfaces or meshes found");

        var projectedCurves = new List<Curve>();
        
        if (breps.Count > 0)
        {
            var result = Curve.ProjectToBrep(curve, breps, directionVec, doc.ModelAbsoluteTolerance);
            if (result != null) projectedCurves.AddRange(result);
        }

        if (meshes.Count > 0)
        {
            var result = Curve.ProjectToMesh(curve, meshes, directionVec, doc.ModelAbsoluteTolerance);
            if (result != null) projectedCurves.AddRange(result);
        }

        if (projectedCurves.Count == 0)
            return new JObject
            {
                ["result_ids"] = new JArray(),
                ["message"] = "Projection failed - no intersections found"
            };

        var resultIds = new JArray();
        foreach (var projCurve in projectedCurves)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddCurve(projCurve, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = projectedCurves.Count,
            ["message"] = $"Projected {projectedCurves.Count} curve(s)"
        };
    }

    /// <summary>
    /// Find intersection points or curves between two curves.
    /// </summary>
    public JObject IntersectCurves(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveIdA = parameters["curve_id_a"]?.ToString();
        var curveIdB = parameters["curve_id_b"]?.ToString();
        var tolerance = parameters["tolerance"]?.ToObject<double>() ?? doc.ModelAbsoluteTolerance;
        var name = parameters["name"]?.ToString();

        if (string.IsNullOrEmpty(curveIdA) || string.IsNullOrEmpty(curveIdB))
            throw new ArgumentException("Intersect requires two curve IDs (curve_id_a and curve_id_b)");

        var objA = doc.Objects.Find(new Guid(curveIdA));
        var objB = doc.Objects.Find(new Guid(curveIdB));

        if (objA == null || objB == null)
            throw new InvalidOperationException("One or both curve objects not found");

        var curveA = objA.Geometry as Curve;
        var curveB = objB.Geometry as Curve;

        if (curveA == null || curveB == null)
            throw new InvalidOperationException("One or both objects are not curves");

        var intersections = Intersection.CurveCurve(curveA, curveB, tolerance, tolerance);

        if (intersections == null || intersections.Count == 0)
            return new JObject
            {
                ["points"] = new JArray(),
                ["point_ids"] = new JArray(),
                ["curve_ids"] = new JArray(),
                ["message"] = "No intersections found"
            };

        var resultPointIds = new JArray();
        var resultCurveIds = new JArray();
        var resultPoints = new JArray();

        foreach (var eventItem in intersections)
        {
            if (eventItem.IsPoint)
            {
                var pt = eventItem.PointA;
                resultPoints.Add(new JArray { pt.X, pt.Y, pt.Z });

                var attr = new ObjectAttributes();
                if (!string.IsNullOrEmpty(name))
                    attr.Name = name + "_point";

                var id = doc.Objects.AddPoint(pt, attr);
                resultPointIds.Add(id.ToString());
            }
            else if (eventItem.IsOverlap)
            {
                // For overlaps, we can extract the overlapping segment from curve A
                var overlapCurve = curveA.Trim(eventItem.ParameterA0, eventItem.ParameterA1);
                if (overlapCurve != null)
                {
                    var attr = new ObjectAttributes();
                    if (!string.IsNullOrEmpty(name))
                        attr.Name = name + "_overlap";

                    var id = doc.Objects.AddCurve(overlapCurve, attr);
                    resultCurveIds.Add(id.ToString());
                }
            }
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["points"] = resultPoints,
            ["point_ids"] = resultPointIds,
            ["curve_ids"] = resultCurveIds,
            ["count"] = intersections.Count,
            ["message"] = $"Found {intersections.Count} intersection(s)"
        };
    }

    /// <summary>
    /// Split a curve at specified parameters or points.
    /// </summary>
    public JObject SplitCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveId = parameters["curve_id"]?.ToString();
        var splitParams = parameters["parameters"]?.ToObject<List<double>>();
        var pointIds = parameters["point_ids"]?.ToObject<List<string>>();
        var deleteSource = parameters["delete_source"]?.ToObject<bool>() ?? true;
        var name = parameters["name"]?.ToString();

        if (string.IsNullOrEmpty(curveId))
            throw new ArgumentException("Split requires a curve_id");

        var curveObj = doc.Objects.Find(new Guid(curveId));
        if (curveObj == null)
            throw new InvalidOperationException($"Curve object with ID {curveId} not found");

        var curve = curveObj.Geometry as Curve;
        if (curve == null)
            throw new InvalidOperationException($"Object {curveId} is not a curve");

        var parametersToSplit = new List<double>();

        if (splitParams != null && splitParams.Count > 0)
        {
            parametersToSplit.AddRange(splitParams);
        }

        if (pointIds != null && pointIds.Count > 0)
        {
            foreach (var idStr in pointIds)
            {
                var obj = doc.Objects.Find(new Guid(idStr));
                if (obj == null) continue;

                Point3d pt;
                if (obj.Geometry is Point point)
                    pt = point.Location;
                else if (obj.Geometry is Point3d dot) // Dot is different, but usually we deal with Point
                    pt = dot;
                else
                    continue;

                double t;
                if (curve.ClosestPoint(pt, out t, doc.ModelAbsoluteTolerance))
                {
                    parametersToSplit.Add(t);
                }
            }
        }

        if (parametersToSplit.Count == 0)
            throw new ArgumentException("No split parameters or points provided");

        var splitCurves = curve.Split(parametersToSplit);

        if (splitCurves == null || splitCurves.Length == 0)
            throw new InvalidOperationException("Split operation failed");

        var resultIds = new JArray();
        foreach (var segment in splitCurves)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddCurve(segment, attr);
            resultIds.Add(id.ToString());
        }

        if (deleteSource)
        {
            doc.Objects.Delete(curveObj, true);
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = splitCurves.Length,
            ["message"] = $"Split curve into {splitCurves.Length} segment(s)"
        };
    }
}
