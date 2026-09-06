using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 var layers=file.AllLayers.Select(l=>new {id=l.Id.ToString(),parent=l.ParentLayerId.ToString(),name=l.Name,index=l.Index,visible=l.IsVisible,locked=l.IsLocked}).ToArray();
 var objects=new List<object>();
 foreach(var o in file.Objects) {
  Brep b=o.Geometry as Brep;if(b==null&&o.Geometry is Extrusion ex)b=ex.ToBrep();if(b==null&&o.Geometry is Surface s)b=s.ToBrep();
  objects.Add(new {name=o.Attributes.Name??"",layer=o.Attributes.LayerIndex,visible=o.Attributes.Visible,mode=o.Attributes.Mode.ToString(),valid=o.Geometry.IsValid,solid=b!=null&&b.IsSolid,nonplanar=b==null?0:b.Faces.Count(f=>!f.IsPlanar(0.01)),naked=b==null?-1:b.Edges.Count(e=>e.Valence==EdgeAdjacency.Naked)});
 }
 output.AppendLine(Serialize(new {layers,objects}));
}
