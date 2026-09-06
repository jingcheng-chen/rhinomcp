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
  var nonplanar=brep==null?new BrepFace[0]:brep.Faces.Where(f=>!f.IsPlanar(0.001)).ToArray();
  bool boundaryPlanes=brep!=null; bool hasBottom=false;
  if(brep!=null) foreach(var f in brep.Faces.Where(f=>f.IsPlanar(0.001))) {
   var fb=f.DuplicateFace(false).GetBoundingBox(true);
   bool onPlane=Math.Abs(fb.Min.Z)<0.001&&Math.Abs(fb.Max.Z)<0.001;
   hasBottom=hasBottom||onPlane;
   foreach(int axis in new[]{0,1}) foreach(double value in new[]{0.0,100.0*SCALE_VALUE})
    onPlane=onPlane||(Math.Abs(fb.Min[axis]-value)<0.001&&Math.Abs(fb.Max[axis]-value)<0.001);
   boundaryPlanes=boundaryPlanes&&onPlane;
  }
  if(nonplanar.Length==1) {
   var face=nonplanar[0]; var s=face.UnderlyingSurface();
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
  var membership=new List<bool>();
  foreach(var p in new Point3d[]{MEMBERSHIP_POINTS}) membership.Add(brep!=null&&brep.IsSolid&&brep.IsPointInside(p,0.001,true));
  double? volume=brep!=null&&brep.IsSolid?VolumeMassProperties.Compute(brep)?.Volume:null;
  objects.Add(new {nonplanar=nonplanar.Length,boundaryPlanes,hasBottom,volume,membership,naked_edges=brep==null?-1:brep.Edges.Count(e=>e.Valence==EdgeAdjacency.Naked),name=o.Attributes.Name,layer=o.Attributes.LayerIndex,visible=o.Attributes.Visible,mode=o.Attributes.Mode.ToString(),valid=o.Geometry.IsValid,faces=brep?.Faces.Count??0,solid=brep!=null&&brep.IsSolid,untrimmed,smooth,min=new[]{b.Min.X,b.Min.Y,b.Min.Z},max=new[]{b.Max.X,b.Max.Y,b.Max.Z},points,distances});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(),layers,objects}));
}
