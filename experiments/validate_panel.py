"""Calibrate the shared panel evaluator with independent Bezier control nets."""

import json
import math
import time
from experiments.bridge import script
from experiments.runner import ROOT, load_task, save, sha256
from experiments.panel_task import measure, evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked

VARIANTS = (
    "correct",
    "reparameterized",
    "flat",
    "wrong_height",
    "wrong_sign",
    "wrong_pose",
    "wrong_scale",
    "extra_object",
    "hidden_extra",
    "wrong_units",
    "clipped",
)


def run():
    directory = (
        ROOT / "experiments/runs" / time.strftime("panel-calibration-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    reports = {}
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        for name in ["raised", "depressed"]:
            task = load_task(ROOT / f"experiments/tasks/panel_{name}.json")
            reports[name] = {}
            for variant in VARIANTS:
                path = directory / f"{name}-{variant}.3dm"
                h = task["panel_height"] * (
                    0
                    if variant == "flat"
                    else 0.7
                    if variant == "wrong_height"
                    else -1
                    if variant == "wrong_sign"
                    else 1
                )
                x, y, z = task["translation"]
                angle = math.radians(task["rotation_x_degrees"])
                code = f"""
using(var f=new Rhino.FileIO.File3dm()){{
f.Settings.ModelUnitSystem=UnitSystem.{"Meters" if variant == "wrong_units" else "Millimeters"};
using(var s=NurbsSurface.Create(3,false,3,3,3,3)){{
for(int i=0;i<4;i++){{s.KnotsU[i]=i<2?0:1;s.KnotsV[i]=i<2?0:1;}}
for(int i=0;i<3;i++)for(int j=0;j<3;j++)s.Points.SetPoint(i,j,new Point3d(i*50,j*40,(i==1&&j==1)?({h})*4:0));
{"s.SetDomain(0,new Interval(-3,7));s.SetDomain(1,new Interval(20,30));" if variant == "reparameterized" else ""}
using(var b={"s.Trim(new Interval(0,0.8),new Interval(0,1)).ToBrep()" if variant == "clipped" else "s.ToBrep()"}){{
{"b.Scale(0.9);" if variant == "wrong_scale" else ""}
b.Transform(Transform.Rotation({angle},Vector3d.XAxis,Point3d.Origin));
b.Transform(Transform.Translation({x + (5 if variant == "wrong_pose" else 0)},{y},{z}));
f.Objects.AddBrep(b,new Rhino.DocObjects.ObjectAttributes());
}}
}}
{"var attr=new Rhino.DocObjects.ObjectAttributes();" + ("attr.Mode=Rhino.DocObjects.ObjectMode.Hidden;" if variant == "hidden_extra" else "") + "f.Objects.AddPoint(Point3d.Origin,attr);" if variant in ["extra_object", "hidden_extra"] else ""}
if(!f.Write({json.dumps(str(path))},8))throw new Exception("Fixture write failed");
}}"""
                (directory / f"{name}-{variant}.cs").write_text(code)
                script(code)
                first = measure(path, task)
                second = measure(path, task)
                report = evaluate(task, first)
                report.update(
                    expected="pass"
                    if variant in ["correct", "reparameterized"]
                    else "fail",
                    repeat_identical=first == second,
                    artifact_sha256=sha256(path),
                )
                reports[name][variant] = report
                save(directory / "results.json", reports)
        require_owned(runtime(), owner)
        if fingerprint() != before:
            raise RuntimeError("Document changed")
        save(directory / "preservation.json", {"preserved": True, "runtime": runtime()})
    for name in [
        "panel_task.py",
        "panel_measure.cs",
        "validate_panel.py",
        "tasks/schema.json",
    ]:
        target = directory / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / "experiments" / name).read_bytes())
    failures = [
        (n, v)
        for n, rows in reports.items()
        for v, r in rows.items()
        if r["status"] != r["expected"] or not r["repeat_identical"]
    ]
    save(
        directory / "summary.json",
        {"fixtures": sum(map(len, reports.values())), "unexpected": failures},
    )
    print(directory)
    if failures:
        raise RuntimeError(str(failures))
    return directory


if __name__ == "__main__":
    run()
