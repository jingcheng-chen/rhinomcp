"""Independent through-hole fixtures, including equal-volume blind holes."""

import json
import time

from experiments.bridge import script
from experiments.evaluator import evaluate
from experiments.runner import ROOT, load_task, measure, save


def validate_hole():
    directory = (
        ROOT / "experiments/runs" / ("evaluator-hole-" + time.strftime("%Y%m%d-%H%M%S"))
    )
    directory.mkdir(parents=True)
    task = load_task(ROOT / "experiments/tasks/through_hole.json")
    reports = {}
    variants = (
        "correct_extrusion",
        "correct_brep",
        "correct_oversized_cutter",
        "wrong_location",
        "wrong_radius",
        "blind",
        "equal_volume_blind",
        "missing_hole",
        "extra_object",
        "open_surface",
        "wrong_units",
    )
    for name in variants:
        path = directory / f"{name}.3dm"
        radius = (
            "Math.Sqrt(48)"
            if name == "equal_volume_blind"
            else "7"
            if name == "wrong_radius"
            else "6"
        )
        code = f"""
using (var model = new Rhino.FileIO.File3dm()) {{
    model.Settings.ModelUnitSystem = UnitSystem.{"Meters" if name == "wrong_units" else "Millimeters"};
    var outer = new Rectangle3d(Plane.WorldXY, new Interval(0,100), new Interval(0,60)).ToNurbsCurve();
    var extrusion = Extrusion.Create(outer, 20, true);
    var hole = new Circle(new Point3d({35 if name == "wrong_location" else 30},20,0), {radius}).ToNurbsCurve();
    hole.Reverse();
    if (!extrusion.AddInnerProfile(hole)) throw new Exception("Reference inner profile failed");
    var solid = extrusion.ToBrep();
    if (!solid.IsValid || !solid.IsSolid) throw new Exception("Reference construction failed");
"""
        if name in (
            "blind",
            "equal_volume_blind",
            "missing_hole",
            "correct_oversized_cutter",
        ):
            code += """
    solid = new Box(Plane.WorldXY, new Interval(0,100), new Interval(0,60), new Interval(0,20)).ToBrep();
"""
            if name != "missing_hole":
                code += f"""
    var cutter = new Cylinder(new Circle(new Point3d(30,20,{-1 if name == "correct_oversized_cutter" else 5}), {radius}), {22 if name == "correct_oversized_cutter" else 20}).ToBrep(true,true);
    var cut = Brep.CreateBooleanDifference(solid, cutter, 0.001);
    if (cut == null || cut.Length != 1) throw new Exception("Blind fixture failed");
    solid = cut[0];
"""
        if name == "correct_extrusion":
            code += "model.Objects.AddExtrusion(extrusion, new Rhino.DocObjects.ObjectAttributes());\n"
        else:
            geometry = (
                "solid.Faces[0].DuplicateFace(false)"
                if name == "open_surface"
                else "solid"
            )
            code += f"model.Objects.AddBrep({geometry}, new Rhino.DocObjects.ObjectAttributes());\n"
        if name == "extra_object":
            code += "model.Objects.AddPoint(new Point3d(0,0,0));\n"
        code += f"""
    if (!model.Write({json.dumps(str(path))}, 8)) throw new Exception("Fixture save failed");
}}
"""
        script(code)
        report = evaluate(task, measure(path))
        repeated = evaluate(task, measure(path))
        report["repeat_identical"] = repeated == report
        save(directory / f"{name}.json", report)
        expected = "pass" if name.startswith("correct_") else "fail"
        if report["status"] != expected or not report["repeat_identical"]:
            raise AssertionError(f"Unexpected {name} verdict: {report}")
        if name == "equal_volume_blind" and not report["checks"]["volume"]:
            raise AssertionError("Blind-hole fixture must preserve the target volume")
        reports[name] = report
    save(directory / "validation.json", reports)
    return directory


if __name__ == "__main__":
    print(validate_hole())
