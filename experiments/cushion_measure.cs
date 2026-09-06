using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 if(file==null) throw new Exception("Cannot read cushion artifact");
 var layers=file.AllLayers.Select(l=>new {id=l.Id.ToString(),parent=l.ParentLayerId.ToString(),name=l.Name,index=l.Index,visible=l.IsVisible,locked=l.IsLocked}).ToArray();
 var objects=new List<object>();
 foreach(var o in file.Objects) {
  var b=o.Geometry.GetBoundingBox(true);
  var brep=o.Geometry as Brep;
  if(brep==null && o.Geometry is Surface surface) brep=surface.ToBrep();
  if(brep==null && o.Geometry is Extrusion ex) brep=ex.ToBrep();
  var points=new List<double[]>(); var distances=new List<double>();
  bool smooth=false,untrimmed=false;
  if(brep!=null && brep.Faces.Count==1) {
   var face=brep.Faces[0]; var s=face.UnderlyingSurface();
   untrimmed=face.IsSurface;
   double t; smooth=!s.GetNextDiscontinuity(0,Continuity.C1_continuous,s.Domain(0).T0,s.Domain(0).T1,out t)
    && !s.GetNextDiscontinuity(1,Continuity.C1_continuous,s.Domain(1).T0,s.Domain(1).T1,out t);
   for(int i=0;i<=40;i++) for(int j=0;j<=40;j++) {
    var p=s.PointAt(s.Domain(0).ParameterAt(i/40.0),s.Domain(1).ParameterAt(j/40.0));
    points.Add(new[]{p.X,p.Y,p.Z});
   }
   foreach(var p in new Point3d[]{EXPECTED_POINTS}) {
    double u,v; distances.Add(s.ClosestPoint(p,out u,out v)?p.DistanceTo(s.PointAt(u,v)):1e99);
   }
  }
  objects.Add(new {name=o.Attributes.Name,layer=o.Attributes.LayerIndex,visible=o.Attributes.Visible,mode=o.Attributes.Mode.ToString(),valid=o.Geometry.IsValid,faces=brep?.Faces.Count??0,solid=brep!=null&&brep.IsSolid,untrimmed,smooth,min=new[]{b.Min.X,b.Min.Y,b.Min.Z},max=new[]{b.Max.X,b.Max.Y,b.Max.Z},points,distances});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(),layers,objects}));
}
