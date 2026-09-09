using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 if(file==null) throw new Exception("Cannot read strip fixture");
 var objects=new List<object>();
 foreach(var obj in file.Objects) {
  Brep brep=obj.Geometry as Brep;
  if(brep==null && obj.Geometry is Extrusion ex) brep=ex.ToBrep();
  if(brep==null) { objects.Add(new {valid=false,solid=false});continue; }
  var originalOrientation=brep.SolidOrientation.ToString();
  // IsPointInside expects outward normals. Normalize only the in-memory judge copy.
  brep=brep.DuplicateBrep();
  if(brep.SolidOrientation==BrepSolidOrientation.Inward) brep.Flip();
  var bounds=brep.GetBoundingBox(true);
  var naked=brep.DuplicateNakedEdgeCurves(true,false);
  var loops=naked.Length==0 ? new Curve[0] : Curve.JoinCurves(naked,0.001);
  var volume=brep.IsSolid ? VolumeMassProperties.Compute(brep) : null;
  var area=AreaMassProperties.Compute(brep);
  var membership=new List<bool>();
  // A fixed grid spanning the expected quarter-annulus and empty surroundings.
  foreach(double z in new[]{-2.0,5.0,12.0})
   foreach(double x in new[]{-20.0,10.0,30.0,50.0,70.0,95.0,105.0,125.0})
    foreach(double y in new[]{-20.0,10.0,30.0,50.0,70.0,95.0,105.0,125.0})
     membership.Add(brep.IsSolid && brep.IsPointInside(new Point3d(x,y,z),0.001,true));
  objects.Add(new {valid=brep.IsValid,solid=brep.IsSolid,orientation=originalOrientation,
   volume=volume==null ? (double?)null : Math.Abs(volume.Volume), area=area.Area,
   min=new[]{bounds.Min.X,bounds.Min.Y,bounds.Min.Z},max=new[]{bounds.Max.X,bounds.Max.Y,bounds.Max.Z},
   naked_edges=naked.Length,naked_loops=loops.Length, membership});
 }
 output.AppendLine(Serialize(new {units=file.Settings.ModelUnitSystem.ToString(),objects}));
}
