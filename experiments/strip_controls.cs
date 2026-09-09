Brep Sector(double radius,double width,double height) {
 double inner=radius-width/2,outer=radius+width/2;
 var boundary=new PolyCurve();
 var a=new Arc(Plane.WorldXY,outer,Math.PI/2).ToNurbsCurve();
 var b=new Arc(Plane.WorldXY,inner,Math.PI/2).ToNurbsCurve();b.Reverse();
 boundary.Append(a);boundary.Append(new LineCurve(a.PointAtEnd,b.PointAtStart));
 boundary.Append(b);boundary.Append(new LineCurve(b.PointAtEnd,a.PointAtStart));
 var side=Surface.CreateExtrusion(boundary,new Vector3d(0,0,height)).ToBrep();
 var solid=side.CapPlanarHoles(0.001);
 if(solid==null || !solid.IsSolid) throw new Exception("Independent sector construction failed");
 return solid;
}
void WriteFixture(string name,params Brep[] geometry) {
 using(var file=new Rhino.FileIO.File3dm()) {
  file.Settings.ModelUnitSystem=UnitSystem.Millimeters;
  foreach(var brep in geometry) file.Objects.AddBrep(brep,new ObjectAttributes());
  if(!file.Write(System.IO.Path.Combine(OUTPUT_DIRECTORY,name+".3dm"),8)) throw new Exception("Fixture save failed");
 }
}
WriteFixture("independent_correct",Sector(100,20,10));
var outward=Sector(100,20,10);
if(outward.SolidOrientation==BrepSolidOrientation.Inward) outward.Flip();
WriteFixture("independent_outward",outward);
WriteFixture("wrong_width",Sector(100,10,10));
WriteFixture("equal_volume_wrong_radius",Sector(120,20,1000.0/120));
var translated=Sector(100,20,10);translated.Transform(Transform.Translation(15,0,0));
WriteFixture("wrong_position",translated);
WriteFixture("extra_object",Sector(100,20,10),new Sphere(new Point3d(30,30,5),2).ToBrep());
