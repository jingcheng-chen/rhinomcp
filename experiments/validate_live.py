"""Prove the evaluator rejects saved, deliberately incorrect Rhino fixtures."""

import json
import time

from experiments.bridge import script
from experiments.evaluator import evaluate
from experiments.runner import ROOT, measure, save


def validate():
    directory = (
        ROOT / "experiments/runs" / ("evaluator-" + time.strftime("%Y%m%d-%H%M%S"))
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


if __name__ == "__main__":
    print(validate())
