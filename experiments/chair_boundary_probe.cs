using(var file=Rhino.FileIO.File3dm.Read(ARTIFACT_PATH)) {
 var o=file.Objects.First(x=>x.Attributes.Name=="back_body");
 var b=o.Geometry as Brep;if(b==null)throw new Exception("Back is not Brep");
 var naked=b.Edges.Where(e=>e.Valence==EdgeAdjacency.Naked).ToArray();
 var reports=new List<object>();
 foreach(var e in naked){
  var pairs=new List<object>();
  foreach(var other in naked.Where(x=>x.EdgeIndex!=e.EdgeIndex)){
   var distances=new List<double>();
   for(int i=0;i<=100;i++){
    var p=e.PointAt(e.Domain.ParameterAt(i/100.0));double t;
    distances.Add(other.ClosestPoint(p,out t)?p.DistanceTo(other.PointAt(t)):1e99);
   }
   pairs.Add(new {edge=other.EdgeIndex,min=distances.Min(),max=distances.Max(),mean=distances.Average()});
  }
  reports.Add(new {edge=e.EdgeIndex,length=e.GetLength(),start=e.PointAtStart,end=e.PointAtEnd,faces=e.AdjacentFaces(),samples=Enumerable.Range(0,11).Select(i=>e.PointAt(e.Domain.ParameterAt(i/10.0))).ToArray(),pairs});
 }
 output.AppendLine(Serialize(new {tolerance=file.Settings.ModelAbsoluteTolerance,valid=b.IsValid,solid=b.IsSolid,edges=reports}));
}
