using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Advanced geometry operations: Loft, Extrude, Sweep, Offset, Pipe
/// </summary>
public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Create a loft surface through multiple curves.
    /// </summary>
    public JObject Loft(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveIds = parameters["curve_ids"]?.ToObject<List<string>>();
        var name = parameters["name"]?.ToString();
        var closed = parameters["closed"]?.ToObject<bool>() ?? false;
        var loftType = parameters["loft_type"]?.ToObject<int>() ?? 0;

        if (curveIds == null || curveIds.Count < 2)
            throw new ArgumentException("Loft requires at least 2 curve IDs");

        var curves = new List<Curve>();
        foreach (var idStr in curveIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null)
                throw new InvalidOperationException($"Object with ID {idStr} not found");

            var curve = obj.Geometry as Curve;
            if (curve == null)
                throw new InvalidOperationException($"Object {idStr} is not a curve");

            curves.Add(curve);
        }

        // Convert loft type
        var loftTypeEnum = loftType switch
        {
            0 => LoftType.Normal,
            1 => LoftType.Loose,
            2 => LoftType.Tight,
            3 => LoftType.Straight,
            4 => LoftType.Developable,
            _ => LoftType.Normal
        };

        var breps = Brep.CreateFromLoft(curves, Point3d.Unset, Point3d.Unset, loftTypeEnum, closed);

        if (breps == null || breps.Length == 0)
            throw new InvalidOperationException("Loft operation failed - ensure curves are valid and compatible");

        var resultIds = new JArray();
        foreach (var brep in breps)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(brep, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = breps.Length,
            ["message"] = $"Loft created {breps.Length} surface(s)"
        };
    }

    /// <summary>
    /// Extrude a curve along a direction vector.
    /// </summary>
    public JObject ExtrudeCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveId = parameters["curve_id"]?.ToString();
        var direction = parameters["direction"]?.ToObject<List<double>>();
        var name = parameters["name"]?.ToString();
        var cap = parameters["cap"]?.ToObject<bool>() ?? true;

        if (string.IsNullOrEmpty(curveId))
            throw new ArgumentException("Extrude requires a curve_id");

        if (direction == null || direction.Count != 3)
            throw new ArgumentException("Extrude requires a direction vector [x, y, z]");

        var obj = doc.Objects.Find(new Guid(curveId));
        if (obj == null)
            throw new InvalidOperationException($"Object with ID {curveId} not found");

        var curve = obj.Geometry as Curve;
        if (curve == null)
            throw new InvalidOperationException($"Object {curveId} is not a curve");

        var directionVec = new Vector3d(direction[0], direction[1], direction[2]);

        // Create extrusion
        Surface extrudedSurface = Surface.CreateExtrusion(curve, directionVec);
        if (extrudedSurface == null)
            throw new InvalidOperationException("Extrusion failed");

        Guid resultId;
        var attr = new ObjectAttributes();
        if (!string.IsNullOrEmpty(name))
            attr.Name = name;

        // If curve is closed and cap is requested, create a capped solid
        if (cap && curve.IsClosed)
        {
            var brep = extrudedSurface.ToBrep();
            if (brep != null)
            {
                var cappedBrep = brep.CapPlanarHoles(doc.ModelAbsoluteTolerance);
                if (cappedBrep != null)
                {
                    resultId = doc.Objects.AddBrep(cappedBrep, attr);
                }
                else
                {
                    resultId = doc.Objects.AddBrep(brep, attr);
                }
            }
            else
            {
                resultId = doc.Objects.AddSurface(extrudedSurface, attr);
            }
        }
        else
        {
            resultId = doc.Objects.AddSurface(extrudedSurface, attr);
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_id"] = resultId.ToString(),
            ["message"] = "Extrusion created successfully"
        };
    }

    /// <summary>
    /// Sweep profile curves along a rail curve.
    /// </summary>
    public JObject Sweep1(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var railId = parameters["rail_id"]?.ToString();
        var profileIds = parameters["profile_ids"]?.ToObject<List<string>>();
        var name = parameters["name"]?.ToString();
        var closed = parameters["closed"]?.ToObject<bool>() ?? false;

        if (string.IsNullOrEmpty(railId))
            throw new ArgumentException("Sweep requires a rail_id");

        if (profileIds == null || profileIds.Count == 0)
            throw new ArgumentException("Sweep requires at least one profile curve");

        // Get rail curve
        var railObj = doc.Objects.Find(new Guid(railId));
        if (railObj == null)
            throw new InvalidOperationException($"Rail object with ID {railId} not found");

        var rail = railObj.Geometry as Curve;
        if (rail == null)
            throw new InvalidOperationException($"Rail object {railId} is not a curve");

        // Get profile curves
        var profiles = new List<Curve>();
        foreach (var idStr in profileIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null)
                throw new InvalidOperationException($"Profile object with ID {idStr} not found");

            var curve = obj.Geometry as Curve;
            if (curve == null)
                throw new InvalidOperationException($"Profile object {idStr} is not a curve");

            profiles.Add(curve);
        }

        // Create sweep
        var sweep = new SweepOneRail();
        sweep.SetToRoadlikeTop();
        var breps = sweep.PerformSweep(rail, profiles);

        if (breps == null || breps.Length == 0)
            throw new InvalidOperationException("Sweep operation failed - ensure rail and profiles are valid");

        var resultIds = new JArray();
        foreach (var brep in breps)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(brep, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = breps.Length,
            ["message"] = $"Sweep created {breps.Length} surface(s)"
        };
    }

    /// <summary>
    /// Offset a curve by a specified distance.
    /// </summary>
    public JObject OffsetCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveId = parameters["curve_id"]?.ToString();
        var distance = parameters["distance"]?.ToObject<double>() ?? 0;
        var name = parameters["name"]?.ToString();
        var planeNormal = parameters["plane"]?.ToObject<List<double>>();
        var cornerStyle = parameters["corner_style"]?.ToObject<int>() ?? 1;

        if (string.IsNullOrEmpty(curveId))
            throw new ArgumentException("Offset requires a curve_id");

        if (Math.Abs(distance) < doc.ModelAbsoluteTolerance)
            throw new ArgumentException("Offset distance is too small");

        var obj = doc.Objects.Find(new Guid(curveId));
        if (obj == null)
            throw new InvalidOperationException($"Object with ID {curveId} not found");

        var curve = obj.Geometry as Curve;
        if (curve == null)
            throw new InvalidOperationException($"Object {curveId} is not a curve");

        // Determine the offset plane
        Plane offsetPlane;
        if (planeNormal != null && planeNormal.Count == 3)
        {
            var normal = new Vector3d(planeNormal[0], planeNormal[1], planeNormal[2]);
            offsetPlane = new Plane(curve.PointAtStart, normal);
        }
        else
        {
            // Try to get the curve's plane, fall back to world XY
            if (!curve.TryGetPlane(out offsetPlane))
            {
                offsetPlane = Plane.WorldXY;
                offsetPlane.Origin = curve.PointAtStart;
            }
        }

        // Convert corner style
        var cornerStyleEnum = cornerStyle switch
        {
            0 => CurveOffsetCornerStyle.None,
            1 => CurveOffsetCornerStyle.Sharp,
            2 => CurveOffsetCornerStyle.Round,
            3 => CurveOffsetCornerStyle.Smooth,
            4 => CurveOffsetCornerStyle.Chamfer,
            _ => CurveOffsetCornerStyle.Sharp
        };

        var offsetCurves = curve.Offset(offsetPlane, distance, doc.ModelAbsoluteTolerance, cornerStyleEnum);

        if (offsetCurves == null || offsetCurves.Length == 0)
            throw new InvalidOperationException("Offset operation failed");

        var resultIds = new JArray();
        foreach (var offsetCurve in offsetCurves)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddCurve(offsetCurve, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = offsetCurves.Length,
            ["message"] = $"Offset created {offsetCurves.Length} curve(s)"
        };
    }

    /// <summary>
    /// Create a pipe along a curve.
    /// </summary>
    public JObject Pipe(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var curveId = parameters["curve_id"]?.ToString();
        var radius = parameters["radius"]?.ToObject<double>() ?? 0;
        var name = parameters["name"]?.ToString();
        var cap = parameters["cap"]?.ToObject<bool>() ?? true;
        var fitRail = parameters["fit_rail"]?.ToObject<bool>() ?? false;

        if (string.IsNullOrEmpty(curveId))
            throw new ArgumentException("Pipe requires a curve_id");

        if (radius <= 0)
            throw new ArgumentException("Pipe radius must be positive");

        var obj = doc.Objects.Find(new Guid(curveId));
        if (obj == null)
            throw new InvalidOperationException($"Object with ID {curveId} not found");

        var curve = obj.Geometry as Curve;
        if (curve == null)
            throw new InvalidOperationException($"Object {curveId} is not a curve");

        // Determine cap type
        var capType = cap ? PipeCapMode.Flat : PipeCapMode.None;

        // Create pipe with constant radius
        var breps = Brep.CreatePipe(
            curve,
            radius,
            localBlending: !fitRail,
            cap: capType,
            fitRail: fitRail,
            absoluteTolerance: doc.ModelAbsoluteTolerance,
            angleToleranceRadians: doc.ModelAngleToleranceRadians
        );

        if (breps == null || breps.Length == 0)
            throw new InvalidOperationException("Pipe operation failed");

        var resultIds = new JArray();
        foreach (var brep in breps)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(brep, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = breps.Length,
            ["message"] = $"Pipe created {breps.Length} object(s)"
        };
    }
}
