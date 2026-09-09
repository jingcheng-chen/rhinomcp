"""Saved-file evaluator for rectangular biquadratic panels in a public pose."""

import json
import math
from experiments.bridge import script
from experiments.evaluator import near


def measurement_code(path, task):
    from experiments.runner import ROOT

    code = (ROOT / "experiments/panel_measure.cs").read_text()
    values = {
        "ARTIFACT_PATH": json.dumps(str(path)),
        "WIDTH_VALUE": repr(task["dimensions"][0]),
        "DEPTH_VALUE": repr(task["dimensions"][1]),
        "HEIGHT_VALUE": repr(task["panel_height"]),
        "ANGLE_VALUE": repr(math.radians(task["rotation_x_degrees"])),
        "TX_VALUE": repr(task["translation"][0]),
        "TY_VALUE": repr(task["translation"][1]),
        "TZ_VALUE": repr(task["translation"][2]),
    }
    for key, value in values.items():
        code = code.replace(key, value)
    return code


def measure(path, task):
    from experiments.runner import sha256

    before = sha256(path)
    result = json.loads(script(measurement_code(path, task)))
    if sha256(path) != before:
        raise RuntimeError("Panel artifact changed during evaluation")
    return result


def evaluate(task, measured):
    rows = measured.get("objects", [])
    obj = rows[0] if len(rows) == 1 else {}
    tol = task["linear_tolerance"]
    w, d, _ = task["dimensions"]
    h = task["panel_height"]
    bounds = obj.get("min", []) + obj.get("max", [])
    checks = {
        "one_object": len(rows) == 1,
        "millimeters": measured.get("units") == "Millimeters",
        "valid": obj.get("valid") is True,
        "single_open_face": obj.get("faces") == 1 and obj.get("solid") is False,
        "one_outer_no_inner_loops": obj.get("outer_loops") == 1
        and obj.get("inner_loops") == 0,
        "local_bounds": len(bounds) == 6
        and all(
            near(a, b, tol) for a, b in zip(bounds, [0, 0, min(0, h), w, d, max(0, h)])
        ),
        "reference_to_surface": near(obj.get("reference_error"), 0, tol),
        "surface_to_reference": near(obj.get("surface_error"), 0, tol),
        "rectangular_boundary": near(obj.get("boundary_error"), 0, tol),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measured,
        "limitation": "41×41 bidirectional samples and 41 samples per edge; not a continuous Hausdorff bound",
    }
