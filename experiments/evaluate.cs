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
            volume = volume
        });
    }
    output.AppendLine(Serialize(new {
        units = model.Settings.ModelUnitSystem.ToString(), objects = rows
    }));
}
