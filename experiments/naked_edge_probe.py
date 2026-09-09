"""Read-only loaded-plugin regression probe for Brep boundary edge reporting."""

import argparse
import json
from pathlib import Path

from experiments.bridge import script
from experiments.rhino_trial import runtime
from experiments.runner import save, sha256
from experiments.strip_probe import fingerprint
from experiments.trial import locked

CODE = r"""
var assembly=AppDomain.CurrentDomain.GetAssemblies().Single(a=>a.GetName().Name=="rhinomcp");
var type=assembly.GetType("RhinoMCPPlugin.Functions.RhinoMCPFunctions");
var instance=Activator.CreateInstance(type);
var method=type.GetMethod("AddBrepMetrics",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
var jsonType=method.GetParameters()[0].ParameterType;
var shapes=new Dictionary<string,Brep>();
var rectangle=new Rectangle3d(Plane.WorldXY,100,70).ToNurbsCurve();
shapes["outer_boundary"]=Brep.CreatePlanarBreps(new Curve[]{rectangle},0.001)[0];
var circle=new Circle(new Point3d(30,30,0),8).ToNurbsCurve();
shapes["one_hole"]=Brep.CreatePlanarBreps(new Curve[]{rectangle,circle},0.001)[0];
var circle2=new Circle(new Point3d(70,30,0),5).ToNurbsCurve();
shapes["two_holes"]=Brep.CreatePlanarBreps(new Curve[]{rectangle,circle,circle2},0.001)[0];
shapes["closed_box"]=new BoundingBox(Point3d.Origin,new Point3d(10,20,30)).ToBrep();
shapes["closed_sphere"]=new Sphere(Point3d.Origin,10).ToBrep();
shapes["open_cylinder_seam"]=new Cylinder(new Circle(Plane.WorldXY,10),20).ToBrep(false,false);
var rows=new List<object>();
foreach(var pair in shapes)using(var b=pair.Value){
 var metrics=Activator.CreateInstance(jsonType);
 method.Invoke(instance,new object[]{metrics,b});
 rows.Add(new {name=pair.Key,valid=b.IsValid,metrics_json=metrics.ToString()});
}
rectangle.Dispose();circle.Dispose();circle2.Dispose();
output.AppendLine(Serialize(rows));
"""

EXPECTED = {
    "outer_boundary": 4,
    "one_hole": 5,
    "two_holes": 6,
    "closed_box": 0,
    "closed_sphere": 0,
    "open_cylinder_seam": 2,
}


def run(output):
    with locked(Path(__file__).parent / "runs/rhino.lock"):
        before = fingerprint()
        owner = runtime()
        rows = json.loads(script(CODE))
        assert fingerprint() == before, "Document changed during read-only probe"
        assert runtime() == owner, "Runtime changed during probe"
        for row in rows:
            row["metrics"] = json.loads(row.pop("metrics_json"))
            row["expected"] = EXPECTED[row["name"]]
            row["pass"] = (
                row["valid"] and row["metrics"]["naked_edge_count"] == row["expected"]
            )
        result = {
            "rows": rows,
            "pass": len(rows) == len(EXPECTED) and all(row["pass"] for row in rows),
            "runtime": owner,
            "plugin_sha256": sha256(Path(owner["assembly"])),
            "document_preserved": True,
        }
        save(output, result)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output)))
