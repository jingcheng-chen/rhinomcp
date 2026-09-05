"""Prove the evaluator rejects saved, deliberately incorrect Rhino fixtures."""

import json
import time

from experiments.bridge import script
from experiments.evaluator import evaluate
from experiments.runner import ROOT, measure, save


def validate_box():
    directory = (
        ROOT / "experiments/runs" / ("evaluator-box-" + time.strftime("%Y%m%d-%H%M%S"))
    )
    directory.mkdir(parents=True)
    task = json.loads((ROOT / "experiments/tasks/box.json").read_text())
    variants = {
        "correct": (100, 0, False, False, "Millimeters"),
        "wrong_scale": (99, 0, False, False, "Millimeters"),
        "wrong_position": (100, 5, False, False, "Millimeters"),
        "extra_object": (100, 0, True, False, "Millimeters"),
        "open_surface": (100, 0, False, True, "Millimeters"),
        "wrong_units": (100, 0, False, False, "Meters"),
    }
    reports = {}
    for name, (width, offset, extra, surface, units) in variants.items():
        path = directory / f"{name}.3dm"
        # Generate fixtures in memory: no additions or changes to the active doc.
        script(f"""
using (var model = new Rhino.FileIO.File3dm()) {{
    model.Settings.ModelUnitSystem = UnitSystem.{units};
    var box = new Box(Plane.WorldXY, new Interval({offset}, {width + offset}),
                      new Interval(0, 50), new Interval(0, 30));
    var brep = box.ToBrep();
    model.Objects.AddBrep({"brep.Faces[0].DuplicateFace(false)" if surface else "brep"},
                          new Rhino.DocObjects.ObjectAttributes());
    {"model.Objects.AddPoint(new Point3d(0,0,0));" if extra else ""}
    if (!model.Write({json.dumps(str(path))}, 8)) throw new Exception("Fixture save failed");
}}
""")
        report = evaluate(task, measure(path))
        repeated = evaluate(task, measure(path))
        report["repeat_identical"] = repeated == report
        expected = "pass" if name == "correct" else "fail"
        if report["status"] != expected or not report["repeat_identical"]:
            raise AssertionError(f"Evaluator did not validate fixture {name}: {report}")
        reports[name] = report
    save(directory / "validation.json", reports)
    return directory


def validate_prism():
    directory = (
        ROOT
        / "experiments/runs"
        / ("evaluator-prism-" + time.strftime("%Y%m%d-%H%M%S"))
    )
    directory.mkdir(parents=True)
    task = json.loads((ROOT / "experiments/tasks/posed_prism.json").read_text())
    reports = {}
    variants = (
        "correct",
        "split_face",
        "wrong_rotation",
        "wrong_translation",
        "mirrored_triangle",
        "wrong_scale",
        "open_surface",
        "extra_object",
        "wrong_units",
    )
    for name in variants:
        path = directory / f"{name}.3dm"
        # Reference construction uses joined planar faces, independently of the
        # production curve-extrusion tool that the modeler is expected to use.
        width = 79 if name == "wrong_scale" else 80
        points = (
            f"new Point3d({width},40,0), new Point3d(0,40,0), new Point3d({width},0,0)"
            if name == "mirrored_triangle"
            else f"new Point3d(0,0,0), new Point3d({width},0,0), new Point3d(0,40,0)"
        )
        bottom = (
            """
    var center = (p[0] + p[1] + p[2]) / 3.0;
    for (int i=0; i<3; i++)
        faces.Add(Brep.CreateFromCornerPoints(p[i], p[(i+1)%3], center, 1e-7));
"""
            if name == "split_face"
            else "faces.Add(Brep.CreateFromCornerPoints(p[0],p[1],p[2],1e-7));"
        )
        script(f"""
using (var model = new Rhino.FileIO.File3dm()) {{
    model.Settings.ModelUnitSystem = UnitSystem.{"Meters" if name == "wrong_units" else "Millimeters"};
    var p = new[] {{ {points} }};
    var q = p.Select(v => v + new Vector3d(0,0,25)).ToArray();
    var faces = new List<Brep>();
    {bottom}
    faces.Add(Brep.CreateFromCornerPoints(q[0],q[1],q[2],1e-7));
    for (int i=0; i<3; i++)
        faces.Add(Brep.CreateFromCornerPoints(p[i],p[(i+1)%3],q[(i+1)%3],q[i],1e-7));
    var joined = Brep.JoinBreps(faces, 1e-7);
    if (joined == null || joined.Length != 1) throw new Exception("Fixture join failed");
    var solid = joined[0];
    if (solid.SolidOrientation == BrepSolidOrientation.Inward) solid.Flip();
    if (!solid.IsValid || !solid.IsSolid) throw new Exception("Fixture construction failed");
    solid.Transform(Transform.Rotation({-30 if name == "wrong_rotation" else 30} * Math.PI/180, Vector3d.ZAxis, Point3d.Origin));
    solid.Transform(Transform.Translation({121 if name == "wrong_translation" else 120},-40,15));
    model.Objects.AddBrep({"solid.Faces[0].DuplicateFace(false)" if name == "open_surface" else "solid"}, new Rhino.DocObjects.ObjectAttributes());
    {"model.Objects.AddPoint(new Point3d(0,0,0));" if name == "extra_object" else ""}
    if (!model.Write({json.dumps(str(path))}, 8)) throw new Exception("Fixture save failed");
}}
""")
        report = evaluate(task, measure(path))
        repeated = evaluate(task, measure(path))
        report["repeat_identical"] = repeated == report
        expected = "pass" if name in ("correct", "split_face") else "fail"
        save(directory / f"{name}.json", report)
        if report["status"] != expected or not report["repeat_identical"]:
            raise AssertionError(f"Evaluator did not validate fixture {name}: {report}")
        reports[name] = report
    save(directory / "validation.json", reports)
    return directory


if __name__ == "__main__":
    print(validate_box())
    print(validate_prism())
