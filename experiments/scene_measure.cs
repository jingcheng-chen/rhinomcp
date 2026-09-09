using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 if(file==null) throw new Exception("Cannot read scene artifact");
 var layers=file.AllLayers.Select(l=>new {id=l.Id.ToString(),parent=l.ParentLayerId.ToString(),name=l.Name,index=l.Index,visible=l.IsVisible,locked=l.IsLocked}).ToArray();
 var objects=new List<object>();
 foreach(var o in file.Objects) {
  var b=o.Geometry.GetBoundingBox(true);
  var brep=o.Geometry as Brep;
  if(brep==null && o.Geometry is Extrusion ex) brep=ex.ToBrep();
  var volume=brep!=null ? VolumeMassProperties.Compute(brep) : null;
  objects.Add(new {id=o.Attributes.ObjectId.ToString(),name=o.Attributes.Name,layer=o.Attributes.LayerIndex,
   visible=o.Attributes.Visible,mode=o.Attributes.Mode.ToString(),valid=o.Geometry.IsValid,
   solid=brep!=null && brep.IsSolid,volume=volume?.Volume,
   planar_faces=brep!=null && brep.Faces.All(f=>f.IsPlanar(0.001)),
   vertices=brep?.Vertices.Select(v=>new[]{v.Location.X,v.Location.Y,v.Location.Z}).ToArray(),
   min=new[]{b.Min.X,b.Min.Y,b.Min.Z},max=new[]{b.Max.X,b.Max.Y,b.Max.Z},
   geometry_crc=o.Geometry.DataCRC(0),attributes=o.Attributes.ToJSON(new Rhino.FileIO.SerializationOptions())});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(),layers,objects}));
}
