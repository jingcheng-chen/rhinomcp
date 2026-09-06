string[] cases={"correct","scaled_correct","open_top","missing_side","unjoined","flat","wrong_bottom","wrong_position","hidden_parent","wrong_assignment","extra_object"};
foreach(var kind in cases) using(var f=new Rhino.FileIO.File3dm()) {
 f.Settings.ModelUnitSystem=Rhino.UnitSystem.Millimeters;
 var root=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Cushion"};f.AllLayers.Add(root);
 var parent=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Upholstery",ParentLayerId=root.Id,IsVisible=kind!="hidden_parent"};f.AllLayers.Add(parent);
 var leaf=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Body",ParentLayerId=parent.Id};f.AllLayers.Add(leaf);
 // Independent tensor-product Bezier control net for a degree-six double lobe.
 // These are Bernstein coefficients, not interpolation points or MCP construction.
 double[] c={0,0,7.2,-10.8,7.2,0,0};
 var s=NurbsSurface.Create(3,false,7,7,7,7);
 for(int i=0;i<12;i++){s.KnotsU[i]=i<6?0:1;s.KnotsV[i]=i<6?0:1;}
 for(int i=0;i<7;i++) for(int j=0;j<7;j++) {
  double z=10+(kind=="flat"?0:kind=="wrong_height"?10:20)*c[i]*c[j];
  if(kind=="no_cross_seam") z=10+20*(i*(6-i)/7.5)*(j*(6-j)/7.5);
  s.Points.SetPoint(i,j,new Point3d(i*100.0/6,j*100.0/6,z));
 }
 var attr=new Rhino.DocObjects.ObjectAttributes{Name="cushion_body",LayerIndex=kind=="wrong_assignment"?f.AllLayers.FindId(parent.Id).Index:f.AllLayers.FindId(leaf.Id).Index};
 double bottom=kind=="wrong_bottom"?3:0;
 var faces=new List<Brep>{s.ToBrep()};
 var corners=new[]{new Point3d(0,0,10),new Point3d(100,0,10),new Point3d(100,100,10),new Point3d(0,100,10)};
 if(kind!="open_top") {
  for(int i=0;i<4;i++) {
   if(kind=="missing_side"&&i==0)continue;
   var a=corners[i];var b=corners[(i+1)%4];
   faces.Add(Brep.CreateFromCornerPoints(a,b,new Point3d(b.X,b.Y,bottom),new Point3d(a.X,a.Y,bottom),0.001));
  }
  faces.Add(Brep.CreateFromCornerPoints(new Point3d(0,0,bottom),new Point3d(0,100,bottom),new Point3d(100,100,bottom),new Point3d(100,0,bottom),0.001));
 }
 var bodies=kind=="unjoined"?faces.ToArray():Brep.JoinBreps(faces,0.001);
 if(bodies==null)throw new Exception("Fixture join failed");
 foreach(var body in bodies) {
  if(body.IsSolid&&body.SolidOrientation==BrepSolidOrientation.Inward)body.Flip();
  if(kind=="scaled_correct")body.Scale(0.75);
  if(kind=="wrong_position")body.Translate(5,0,0);
  f.Objects.AddBrep(body,attr);
 }
 if(kind=="extra_object")f.Objects.AddPoint(new Point3d(50,50,10),attr);
 if(!f.Write(System.IO.Path.Combine(OUTPUT_DIRECTORY,kind+".3dm"),8))throw new Exception("Fixture save failed");
}
