using(var file = Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 if(file == null) throw new Exception("Cannot read saved model");
 var objects = new List<object>();
 var overall = BoundingBox.Empty;
 foreach(var obj in file.Objects) {
  var g=obj.Geometry; var box=g.GetBoundingBox(true); overall.Union(box);
  Brep brep=g as Brep;
  if(g is Extrusion ex) brep=ex.ToBrep();
  var volume=brep != null && brep.IsSolid ? VolumeMassProperties.Compute(brep) : null;
  objects.Add(new {name=obj.Attributes.Name ?? "", type=g.ObjectType.ToString(),
   valid=g.IsValid, solid=brep != null && brep.IsSolid,
   volume=volume == null ? (double?)null : Math.Abs(volume.Volume),
   min=new[]{box.Min.X,box.Min.Y,box.Min.Z}, max=new[]{box.Max.X,box.Max.Y,box.Max.Z}});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(), objects,
  dimensions=overall.IsValid ? new[]{overall.Max.X-overall.Min.X,overall.Max.Y-overall.Min.Y,overall.Max.Z-overall.Min.Z} : new[]{0.0,0.0,0.0}}));
}
