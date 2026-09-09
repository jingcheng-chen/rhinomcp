using(var model=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
var rows=new List<object>();
double w=WIDTH_VALUE,d=DEPTH_VALUE,hx=HX_VALUE,hy=HY_VALUE,r=RADIUS_VALUE,tol=TOL_VALUE;
foreach(var item in model.Objects) {
var source=item.Geometry as Brep;
if(source==null){rows.Add(new {valid=false});continue;}
using(var b=source.DuplicateBrep()) {
b.Transform(Transform.Translation(-(TX_VALUE),-(TY_VALUE),-(TZ_VALUE)));
b.Transform(Transform.Rotation(-(ANGLE_VALUE),Vector3d.XAxis,Point3d.Origin));
var box=b.GetBoundingBox(true);double outer=1e99,inner=1e99,area=-1;
int errors=0,samples=0;bool planar=false;
if(b.Faces.Count==1){
var face=b.Faces[0];planar=face.IsPlanar(tol);
using(var amp=AreaMassProperties.Compute(b)){if(amp!=null)area=amp.Area;}
foreach(var loop in b.Loops)using(var curve=loop.To3dCurve()){
if(curve==null)continue;
double error=0;
for(int i=0;i<=128;i++){
var p=curve.PointAt(curve.Domain.ParameterAt(i/128.0));
double e=loop.LoopType==BrepLoopType.Inner?Math.Abs(Math.Sqrt((p.X-hx)*(p.X-hx)+(p.Y-hy)*(p.Y-hy))-r):Math.Min(Math.Min(Math.Abs(p.X),Math.Abs(p.X-w)),Math.Min(Math.Abs(p.Y),Math.Abs(p.Y-d)));
error=Math.Max(error,Math.Max(e,Math.Abs(p.Z)));
}
if(loop.LoopType==BrepLoopType.Outer)outer=error;
if(loop.LoopType==BrepLoopType.Inner)inner=error;
}
for(int i=0;i<=40;i++)for(int j=0;j<=40;j++){
double x=w*(i+0.5)/41.0,y=d*(j+0.5)/41.0,dist=Math.Sqrt((x-hx)*(x-hx)+(y-hy)*(y-hy));
if(Math.Abs(dist-r)<tol*2)continue;
double u,v;bool present=false;
if(face.ClosestPoint(new Point3d(x,y,0),out u,out v))present=face.PointAt(u,v).DistanceTo(new Point3d(x,y,0))<=tol && face.IsPointOnFace(u,v,tol)!=PointFaceRelation.Exterior;
if(present!=(dist>r))errors++;samples++;
}
}
rows.Add(new {valid=b.IsValid,solid=b.IsSolid,faces=b.Faces.Count,planar=planar,
outer_loops=b.Loops.Count(l=>l.LoopType==BrepLoopType.Outer),inner_loops=b.Loops.Count(l=>l.LoopType==BrepLoopType.Inner),
min=new[]{box.Min.X,box.Min.Y,box.Min.Z},max=new[]{box.Max.X,box.Max.Y,box.Max.Z},outer_error=outer,inner_error=inner,area=area,membership_errors=errors,membership_samples=samples});
}
}
output.AppendLine(Serialize(new {units=model.Settings.ModelUnitSystem.ToString(),objects=rows}));
}
