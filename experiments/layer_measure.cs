using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 if(file==null) throw new Exception("Cannot read layer artifact");
 var layers=file.AllLayers.Select(l=>new {id=l.Id.ToString(),parent=l.ParentLayerId.ToString(),name=l.Name,index=l.Index,visible=l.IsVisible,locked=l.IsLocked}).ToArray();
 var objects=new List<object>();
 foreach(var o in file.Objects) {
  var b=o.Geometry.GetBoundingBox(true);
  var brep=o.Geometry as Brep;
  if(brep==null && o.Geometry is Extrusion ex) brep=ex.ToBrep();
  objects.Add(new {name=o.Attributes.Name,layer=o.Attributes.LayerIndex,visible=o.Attributes.Visible,mode=o.Attributes.Mode.ToString(),valid=o.Geometry.IsValid,solid=brep!=null && brep.IsSolid,min=new[]{b.Min.X,b.Min.Y,b.Min.Z},max=new[]{b.Max.X,b.Max.Y,b.Max.Z}});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(),layers,objects}));
}
