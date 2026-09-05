// Trusted controller script: evaluate the saved artifact, not the live document.
using (var model = Rhino.FileIO.File3dm.Read(ARTIFACT_PATH))
{
    if (model == null) throw new Exception("Cannot read candidate artifact");
    var rows = new List<object>();
    foreach (var obj in model.Objects)
    {
        var g = obj.Geometry;
        var box = g.GetBoundingBox(true);
        var brep = g as Brep;
        if (brep == null && g is Extrusion) brep = ((Extrusion)g).ToBrep();
        double? volume = null;
        double? area = null;
        var vertices = new List<double[]>();
        var faceGeometry = new List<object>();
        bool? planarFaces = null;
        bool? straightEdges = null;
        if (brep != null)
        {
            // Split kinked extrusion sides for inspection only. Never rewrite the artifact.
            brep.Faces.SplitKinkyFaces(1e-6, true);
            foreach (var v in brep.Vertices)
                vertices.Add(new[] { v.Location.X, v.Location.Y, v.Location.Z });
            planarFaces = brep.Faces.All(f => f.IsPlanar(1e-7));
            straightEdges = brep.Edges.All(e => e.IsLinear(1e-7));
            foreach (var face in brep.Faces)
            {
                Plane plane;
                Cylinder cylinder;
                if (face.TryGetPlane(out plane, 1e-7))
                    faceGeometry.Add(new { kind = "plane",
                        origin = new[] { plane.Origin.X, plane.Origin.Y, plane.Origin.Z },
                        normal = new[] { plane.Normal.X, plane.Normal.Y, plane.Normal.Z } });
                else if (face.TryGetCylinder(out cylinder, 1e-7))
                {
                    // BrepFace bounds can include the underlying untrimmed cutter
                    // (-1..21 for a hole trimmed to 0..20). Measure the actual face.
                    BoundingBox extent;
                    using (var trimmed = face.DuplicateFace(false))
                        extent = trimmed.GetBoundingBox(true);
                    var center = cylinder.Center;
                    var line = new LineCurve(new Point3d(center.X, center.Y, box.Min.Z-1),
                                             new Point3d(center.X, center.Y, box.Max.Z+1));
                    Curve[] overlaps;
                    Point3d[] hits;
                    bool probeOk = Rhino.Geometry.Intersect.Intersection.CurveBrep(
                        line, brep, 1e-7, out overlaps, out hits);
                    faceGeometry.Add(new { kind = "cylinder", radius = cylinder.Radius,
                        center = new[] { center.X, center.Y, center.Z },
                        axis = new[] { cylinder.Axis.X, cylinder.Axis.Y, cylinder.Axis.Z },
                        z_range = new[] { extent.Min.Z, extent.Max.Z },
                        axis_probe_ok = probeOk,
                        axis_hits = hits == null ? -1 : hits.Length,
                        axis_overlaps = overlaps == null ? -1 : overlaps.Length });
                    line.Dispose();
                    if (overlaps != null) foreach (var overlap in overlaps) overlap.Dispose();
                }
                else faceGeometry.Add(new { kind = "unsupported" });
            }
            using (var mass = AreaMassProperties.Compute(brep))
                if (mass != null) area = mass.Area;
        }
        if (brep != null && brep.IsSolid)
        {
            using (var mass = VolumeMassProperties.Compute(brep))
                if (mass != null) volume = mass.Volume;
        }
        rows.Add(new {
            valid = g.IsValid,
            solid = brep != null && brep.IsSolid,
            minimum = new[] { box.Min.X, box.Min.Y, box.Min.Z },
            dimensions = new[] { box.Max.X-box.Min.X, box.Max.Y-box.Min.Y, box.Max.Z-box.Min.Z },
            volume = volume, area = area, vertices = vertices,
            planar_faces = planarFaces, straight_edges = straightEdges, faces = faceGeometry
        });
    }
    output.AppendLine(Serialize(new {
        units = model.Settings.ModelUnitSystem.ToString(), objects = rows
    }));
}
