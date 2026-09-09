foreach(var variant in new[]{"correct","flat","wrong_parent","wrong_assignment","hidden_parent","locked_child","default_object","extra_object","wrong_geometry"}) {
 using(var f=new Rhino.FileIO.File3dm()) {
  f.Settings.ModelUnitSystem=UnitSystem.Millimeters;
  Func<string,Guid,int> add=(name,parent)=> { var l=new Layer {Id=Guid.NewGuid(),Name=name,ParentLayerId=parent}; f.AllLayers.Add(l); return f.AllLayers.FindId(l.Id).Index; };
  int d=add("Default",Guid.Empty),root=add("Assembly",Guid.Empty);
  int a=add("Left",variant=="flat"?Guid.Empty:f.AllLayers.FindIndex(root).Id);
  int b=add("Right",f.AllLayers.FindIndex(root).Id);
  int x=add("Part",f.AllLayers.FindIndex(a).Id),y=add("Part",f.AllLayers.FindIndex(b).Id);
  if(variant=="wrong_parent") f.AllLayers.FindIndex(b).ParentLayerId=f.AllLayers.FindIndex(a).Id;
  if(variant=="hidden_parent") f.AllLayers.FindIndex(root).IsVisible=false;
  if(variant=="locked_child") f.AllLayers.FindIndex(y).IsLocked=true;
  for(int i=0;i<2;i++) {
   var attrs=new ObjectAttributes {Name=i==0?"left_part":"right_part",LayerIndex=i==0?x:y};
   if(variant=="wrong_assignment" && i==1) attrs.LayerIndex=x;
   if(variant=="default_object" && i==1) attrs.LayerIndex=d;
   double size=variant=="wrong_geometry" && i==1?9:10;
   var box=new BoundingBox(new Point3d(i*30,0,0),new Point3d(i*30+size,10,10));
   f.Objects.AddBrep(box.ToBrep(),attrs);
  }
  if(variant=="extra_object") f.Objects.AddPoint(Point3d.Origin,new ObjectAttributes {LayerIndex=d});
  if(!f.Write(System.IO.Path.Combine(OUTPUT_DIRECTORY,variant+".3dm"),8)) throw new Exception("Fixture write failed");
 }
}
