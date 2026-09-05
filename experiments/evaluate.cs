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
            planar_faces = planarFaces, straight_edges = straightEdges
        });
    }
    output.AppendLine(Serialize(new {
        units = model.Settings.ModelUnitSystem.ToString(), objects = rows
    }));
}
