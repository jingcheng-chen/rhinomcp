// Read saved geometry and transform only a deep copy into the analytic task frame.
using(var model=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
var rows=new List<object>();
double w=WIDTH_VALUE,d=DEPTH_VALUE,h=HEIGHT_VALUE;
Func<double,double,double> height=(x,y)=>16*h*(x/w)*(1-x/w)*(y/d)*(1-y/d);
foreach(var item in model.Objects) {
var source=item.Geometry as Brep;
if(source==null) {rows.Add(new {valid=false});continue;}
using(var b=source.DuplicateBrep()) {
b.Transform(Transform.Translation(-(TX_VALUE),-(TY_VALUE),-(TZ_VALUE)));
b.Transform(Transform.Rotation(-(ANGLE_VALUE),Vector3d.XAxis,Point3d.Origin));
var box=b.GetBoundingBox(true);double forward=1e99,reverse=1e99,boundary=1e99;
if(b.Faces.Count==1) {
var s=b.Faces[0];forward=0;reverse=0;boundary=0;
for(int i=0;i<=40;i++) for(int j=0;j<=40;j++) {
double x=w*i/40.0,y=d*j/40.0;var p=new Point3d(x,y,height(x,y));
double u,v;
forward=Math.Max(forward,s.ClosestPoint(p,out u,out v)?p.DistanceTo(s.PointAt(u,v)):1e99);
var q=s.PointAt(s.Domain(0).ParameterAt(i/40.0),s.Domain(1).ParameterAt(j/40.0));
reverse=Math.Max(reverse,Math.Max(Math.Abs(q.Z-height(q.X,q.Y)),Math.Max(Math.Max(-q.X,q.X-w),Math.Max(-q.Y,q.Y-d))));
}
foreach(var edge in b.Edges)for(int i=0;i<=40;i++) {
var p=edge.PointAt(edge.Domain.ParameterAt(i/40.0));
double border=Math.Min(Math.Min(Math.Abs(p.X),Math.Abs(p.X-w)),Math.Min(Math.Abs(p.Y),Math.Abs(p.Y-d)));
boundary=Math.Max(boundary,Math.Max(Math.Abs(p.Z),border));
}
}
rows.Add(new {valid=b.IsValid,solid=b.IsSolid,faces=b.Faces.Count,
outer_loops=b.Loops.Count(l=>l.LoopType==BrepLoopType.Outer),inner_loops=b.Loops.Count(l=>l.LoopType==BrepLoopType.Inner),
min=new[]{box.Min.X,box.Min.Y,box.Min.Z},max=new[]{box.Max.X,box.Max.Y,box.Max.Z},reference_error=forward,surface_error=reverse,boundary_error=boundary});
}
}
output.AppendLine(Serialize(new {units=model.Settings.ModelUnitSystem.ToString(),objects=rows}));
}
