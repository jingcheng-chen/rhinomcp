"""Independent saved-file checks for a posed planar patch with a circular opening."""

import json
import math
from experiments.bridge import script
from experiments.evaluator import near


def measurement_code(path, task):
    from experiments.runner import ROOT

    code = (ROOT / "experiments/trimmed_measure.cs").read_text()
    values = {
        "ARTIFACT_PATH": json.dumps(str(path)),
        "WIDTH_VALUE": task["dimensions"][0],
        "DEPTH_VALUE": task["dimensions"][1],
        "HX_VALUE": task["hole_center"][0],
        "HY_VALUE": task["hole_center"][1],
        "RADIUS_VALUE": task["hole_radius"],
        "ANGLE_VALUE": math.radians(task["rotation_x_degrees"]),
        "TX_VALUE": task["translation"][0],
        "TY_VALUE": task["translation"][1],
        "TZ_VALUE": task["translation"][2],
        "TOL_VALUE": task["linear_tolerance"],
    }
    for key, value in values.items():
        code = code.replace(key, str(value))
    return code


def measure(path, task):
    from experiments.runner import sha256

    before = sha256(path)
    result = json.loads(script(measurement_code(path, task)))
    if sha256(path) != before:
        raise RuntimeError("Trimmed artifact changed during evaluation")
    return result


def evaluate(task, measured):
    rows = measured.get("objects", [])
    obj = rows[0] if len(rows) == 1 else {}
    w, d, _ = task["dimensions"]
    tol = task["linear_tolerance"]
    bounds = obj.get("min", []) + obj.get("max", [])
    checks = {
        "one_object": len(rows) == 1,
        "millimeters": measured.get("units") == "Millimeters",
        "valid": obj.get("valid") is True,
        "one_open_planar_face": obj.get("faces") == 1
        and obj.get("solid") is False
        and obj.get("planar") is True,
        "outer_and_hole": obj.get("outer_loops") == 1 and obj.get("inner_loops") == 1,
        "local_bounds": len(bounds) == 6
        and all(near(a, b, tol) for a, b in zip(bounds, [0, 0, 0, w, d, 0])),
        "rectangular_outer_boundary": near(obj.get("outer_error"), 0, tol),
        "circular_inner_boundary": near(obj.get("inner_error"), 0, tol),
        "trimmed_area": near(
            obj.get("area"),
            w * d - math.pi * task["hole_radius"] ** 2,
            task["area_tolerance"],
        ),
        "trimmed_membership": obj.get("membership_errors") == 0
        and obj.get("membership_samples", 0) > 100,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measured,
        "limitation": "129 points per loop and a 41x41 occupancy grid; finite sampling, not a continuous shape guarantee.",
    }
