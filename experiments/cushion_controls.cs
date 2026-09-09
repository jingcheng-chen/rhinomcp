string[] cases={"correct","reparameterized","flat","no_cross_seam","wrong_height","wrong_position","wrong_scale","split_panels","faceted","hidden_parent","wrong_assignment","extra_object"};
foreach(var kind in cases) using(var f=new Rhino.FileIO.File3dm()) {
 f.Settings.ModelUnitSystem=Rhino.UnitSystem.Millimeters;
 var root=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Cushion"};f.AllLayers.Add(root);
 var parent=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Upholstery",ParentLayerId=root.Id,IsVisible=kind!="hidden_parent"};f.AllLayers.Add(parent);
 var leaf=new Rhino.DocObjects.Layer{Id=Guid.NewGuid(),Name="Top",ParentLayerId=parent.Id};f.AllLayers.Add(leaf);
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
 if(kind=="reparameterized"){s.SetDomain(0,new Interval(-5,7));s.SetDomain(1,new Interval(20,25));}
 if(kind=="wrong_position")s.Translate(5,0,0);
 if(kind=="wrong_scale")s.Scale(0.9);
 var attr=new Rhino.DocObjects.ObjectAttributes{Name="cushion_top",LayerIndex=kind=="wrong_assignment"?f.AllLayers.FindId(parent.Id).Index:f.AllLayers.FindId(leaf.Id).Index};
 if(kind=="split_panels") {
  f.Objects.AddSurface(s.Trim(new Interval(0,.5),new Interval(0,1)),attr);
  f.Objects.AddSurface(s.Trim(new Interval(.5,1),new Interval(0,1)),attr);
 } else if(kind=="faceted") {
  var pts=new List<Point3d>();for(int i=0;i<=8;i++)for(int j=0;j<=8;j++)pts.Add(s.PointAt(i/8.0,j/8.0));
  f.Objects.AddSurface(NurbsSurface.CreateThroughPoints(pts,9,9,1,1,false,false),attr);
 } else f.Objects.AddSurface(s,attr);
 if(kind=="extra_object")f.Objects.AddPoint(new Point3d(50,50,10),attr);
 if(!f.Write(System.IO.Path.Combine(OUTPUT_DIRECTORY,kind+".3dm"),8))throw new Exception("Fixture save failed");
}
