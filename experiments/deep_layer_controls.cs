foreach(var variant in new[]{"correct","flattened_support","wrong_assignment","hidden_support","locked_leaf","default_object","extra_object","missing_part","wrong_bounds","extra_layer"}) {
 using(var f=new Rhino.FileIO.File3dm()) {
  f.Settings.ModelUnitSystem=UnitSystem.Millimeters;
  Func<string,Guid,int> add=(name,parent)=> {var layer=new Layer {Id=Guid.NewGuid(),Name=name,ParentLayerId=parent}; f.AllLayers.Add(layer); return f.AllLayers.FindId(layer.Id).Index;};
  int d=add("Default",Guid.Empty), root=add("Stand",Guid.Empty);
  int left=add("Left",f.AllLayers.FindIndex(root).Id),right=add("Right",f.AllLayers.FindIndex(root).Id),top=add("Top",f.AllLayers.FindIndex(root).Id);
  int ls=add("Support",f.AllLayers.FindIndex(left).Id),rs=add("Support",f.AllLayers.FindIndex(right).Id);
  int lp=add("Part",f.AllLayers.FindIndex(ls).Id),rp=add("Part",f.AllLayers.FindIndex(rs).Id),tp=add("Part",f.AllLayers.FindIndex(top).Id);
  if(variant=="flattened_support") f.AllLayers.FindIndex(rs).ParentLayerId=f.AllLayers.FindIndex(root).Id;
  if(variant=="hidden_support") f.AllLayers.FindIndex(rs).IsVisible=false;
  if(variant=="locked_leaf") f.AllLayers.FindIndex(lp).IsLocked=true;
  if(variant=="extra_layer") add("Unused",f.AllLayers.FindIndex(root).Id);
  var names=new[]{"left_post","right_post","top"};
  var minima=new[]{new Point3d(0,0,0),new Point3d(60,0,0),new Point3d(-5,-5,40)};
  var maxima=new[]{new Point3d(10,20,40),new Point3d(70,20,40),new Point3d(75,25,50)};
  var indices=new[]{lp,rp,tp};
  for(int i=0;i<3;i++) {
   if(variant=="missing_part" && i==2) continue;
   var attrs=new ObjectAttributes {Name=names[i],LayerIndex=indices[i]};
   if(variant=="wrong_assignment" && i==1) attrs.LayerIndex=lp;
   if(variant=="default_object" && i==2) attrs.LayerIndex=d;
   if(variant=="wrong_bounds" && i==1) maxima[i]=new Point3d(69,20,40);
   f.Objects.AddBrep(new BoundingBox(minima[i],maxima[i]).ToBrep(),attrs);
  }
  if(variant=="extra_object") f.Objects.AddPoint(Point3d.Origin,new ObjectAttributes {LayerIndex=d});
  if(!f.Write(System.IO.Path.Combine(OUTPUT_DIRECTORY,variant+".3dm"),8)) throw new Exception("Deep fixture save failed");
 }
}
