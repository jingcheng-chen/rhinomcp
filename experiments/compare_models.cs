var savedViews=doc.Views.Select(v=>new {view=v,projection=new Rhino.DocObjects.ViewportInfo(v.ActiveViewport),target=v.ActiveViewport.CameraTarget,name=v.ActiveViewport.Name,mode=v.ActiveViewport.DisplayMode.Id}).ToArray();
var original=doc.Objects.Where(o=>o!=null&&!o.IsDeleted).Select(o=>new {id=o.Id,hidden=o.IsHidden}).ToArray();
var added=new List<Guid>(); var groups=new List<List<Guid>>(); var bounds=BoundingBox.Empty;
var reports=new List<object>();
try {
 foreach(var o in original) if(!o.hidden) doc.Objects.Hide(o.id,true);
 foreach(var filename in new[]{BASELINE_PATH,CANDIDATE_PATH}) using(var file=Rhino.FileIO.File3dm.Read(filename)) {
  if(file==null)throw new Exception("Cannot read comparison model");
  var box=BoundingBox.Empty;foreach(var o in file.Objects)box.Union(o.Geometry.GetBoundingBox(true));
  var transform=Transform.Translation(-box.Center.X,-box.Center.Y,-box.Min.Z);
  var ids=new List<Guid>();
  foreach(var o in file.Objects) {
   var g=o.Geometry.Duplicate();g.Transform(transform);bounds.Union(g.GetBoundingBox(true));
   var a=o.Attributes.Duplicate();a.ObjectId=Guid.NewGuid();a.LayerIndex=doc.Layers.CurrentLayerIndex;a.ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject;a.ObjectColor=System.Drawing.Color.FromArgb(180,180,180);a.Visible=true;a.Mode=Rhino.DocObjects.ObjectMode.Normal;
   var id=doc.Objects.Add(g,a);if(id==Guid.Empty)throw new Exception("Comparison copy failed");added.Add(id);ids.Add(id);
  }
  groups.Add(ids);
 }
 double padding=Math.Max(bounds.Diagonal.X,Math.Max(bounds.Diagonal.Y,bounds.Diagonal.Z))*.25;
 bounds.Inflate(padding);
 foreach(var name in new[]{"Perspective","Front","Right"}) {
  var view=doc.Views.FirstOrDefault(v=>v.ActiveViewport.Name.Equals(name,StringComparison.OrdinalIgnoreCase));
  if(view==null)throw new Exception("Comparison viewport missing: "+name);
  var vp=view.ActiveViewport;
  vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.ShadedId);
  foreach(var id in added)doc.Objects.Show(id,true);
  doc.Views.Redraw();Rhino.RhinoApp.Wait();
  vp.ZoomBoundingBox(bounds);
  var projection=new Rhino.DocObjects.ViewportInfo(vp);var target=vp.CameraTarget;
  var frames=new List<object>();
  for(int i=0;i<2;i++) {
   for(int j=0;j<2;j++)foreach(var id in groups[j]) {if(j==i)doc.Objects.Show(id,true);else doc.Objects.Hide(id,true);}
   doc.Views.Redraw();Rhino.RhinoApp.Wait();vp.SetViewProjection(projection,false);vp.SetCameraTarget(target,false);
   using(var image=view.CaptureToBitmap(new System.Drawing.Size(1000,750),false,false,false)) {
    if(image==null)throw new Exception("Comparison capture failed");
    image.Save(System.IO.Path.Combine(OUTPUT_DIRECTORY,(i==0?"baseline-":"candidate-")+name.ToLowerInvariant()+".png"),System.Drawing.Imaging.ImageFormat.Png);
   }
   double fl,fr,fb,ft,fn,ff;vp.GetFrustum(out fl,out fr,out fb,out ft,out fn,out ff);
   frames.Add(new {frustum=new[]{fl,fr,fb,ft,fn,ff},location=vp.CameraLocation,direction=vp.CameraDirection,up=vp.CameraUp,target=vp.CameraTarget,parallel=vp.IsParallelProjection});
  }
  reports.Add(new {view=name,frames});
 }
 output.AppendLine(Serialize(reports));
} finally {
 foreach(var id in added)doc.Objects.Delete(id,true);
 foreach(var o in original)if(!o.hidden)doc.Objects.Show(o.id,true);
 doc.Views.Redraw();Rhino.RhinoApp.Wait();
 foreach(var v in savedViews){var vp=v.view.ActiveViewport;vp.SetViewProjection(v.projection,false);vp.SetCameraTarget(v.target,false);vp.Name=v.name;vp.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(v.mode);}
}
