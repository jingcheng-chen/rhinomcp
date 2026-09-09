"""Calibrate planar trimmed patches from independent boundary-curve fixtures."""

import json
import math
import time
from experiments.bridge import script
from experiments.runner import ROOT, load_task, save, sha256
from experiments.trimmed_task import measure, evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked

VARIANTS = (
    "correct",
    "reversed_loops",
    "wrong_radius",
    "wrong_hole_location",
    "missing_hole",
    "wrong_pose",
    "wrong_scale",
    "extra_object",
    "hidden_extra",
    "wrong_units",
    "solid",
    "clipped",
)


def fixture_code(path, task, variant):
    w, d, _ = task["dimensions"]
    hx, hy = task["hole_center"]
    r = task["hole_radius"]
    x, y, z = task["translation"]
    angle = math.radians(task["rotation_x_degrees"])
    if variant == "wrong_radius":
        r *= 0.8
    if variant == "wrong_hole_location":
        hx += 5
    if variant == "clipped":
        w *= 0.9
    return f"""
using(var f=new Rhino.FileIO.File3dm()){{
f.Settings.ModelUnitSystem=UnitSystem.{"Meters" if variant == "wrong_units" else "Millimeters"};
var outer=new PolylineCurve(new []{{new Point3d(0,0,0),new Point3d({w},0,0),new Point3d({w},{d},0),new Point3d(0,{d},0),new Point3d(0,0,0)}});
var hole=new Circle(new Point3d({hx},{hy},0),{r}).ToNurbsCurve();
{"outer.Reverse();hole.Reverse();" if variant == "reversed_loops" else ""}
var loops=new List<Curve>{{outer}};
{"" if variant == "missing_hole" else "loops.Add(hole);"}
var patches=Brep.CreatePlanarBreps(loops,0.001);
if(patches==null||patches.Length!=1)throw new Exception("Fixture construction failed");
using(var b=patches[0]){{

{"b.Scale(0.9);" if variant == "wrong_scale" else ""}
b.Transform(Transform.Rotation({angle},Vector3d.XAxis,Point3d.Origin));
b.Transform(Transform.Translation({x + (5 if variant == "wrong_pose" else 0)},{y},{z}));
f.Objects.AddBrep(b,new Rhino.DocObjects.ObjectAttributes());
}}
{"f.Objects.Clear();f.Objects.AddBrep(new BoundingBox(0,0,0,10,10,10).ToBrep(),new Rhino.DocObjects.ObjectAttributes());" if variant == "solid" else ""}
{"var attr=new Rhino.DocObjects.ObjectAttributes();" + ("attr.Mode=Rhino.DocObjects.ObjectMode.Hidden;" if variant == "hidden_extra" else "") + "f.Objects.AddPoint(Point3d.Origin,attr);" if variant in ("extra_object", "hidden_extra") else ""}
if(!f.Write({json.dumps(str(path))},8))throw new Exception("Fixture write failed");
outer.Dispose();hole.Dispose();
}}"""


def run():
    directory = (
        ROOT / "experiments/runs" / time.strftime("trimmed-calibration-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    reports = {}
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        for name in ("offset", "reserved"):
            task = load_task(ROOT / f"experiments/tasks/trimmed_{name}.json")
            reports[name] = {}
            for variant in VARIANTS:
                path = directory / f"{name}-{variant}.3dm"
                code = fixture_code(path, task, variant)
                (directory / f"{name}-{variant}.cs").write_text(code)
                script(code)
                first = measure(path, task)
                second = measure(path, task)
                report = evaluate(task, first)
                report.update(
                    expected="pass"
                    if variant in ("correct", "reversed_loops")
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
    for name in (
        "trimmed_task.py",
        "trimmed_measure.cs",
        "validate_trimmed.py",
        "tasks/schema.json",
        "tasks/trimmed_offset.json",
        "tasks/trimmed_reserved.json",
    ):
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
    print(directory, flush=True)
    if failures:
        raise RuntimeError(str(failures))
    return directory


if __name__ == "__main__":
    run()
