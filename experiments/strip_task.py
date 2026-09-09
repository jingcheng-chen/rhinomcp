"""Fixed quarter-annular task with a public translation; independent saved-file judge."""

import json
import math

from experiments.bridge import script


def measurement_code(path, task):
    from experiments.runner import ROOT

    code = (ROOT / "experiments/strip_measure.cs").read_text()
    anchor = "  var originalOrientation=brep.SolidOrientation.ToString();"
    if code.count(anchor) != 1:
        raise ValueError("Strip measurement template changed")
    x, y, z = task["translation"]
    # Transform only an in-memory duplicate, never the saved artifact/document.
    return code.replace("ARTIFACT_PATH", json.dumps(str(path))).replace(
        anchor,
        f"  brep=brep.DuplicateBrep();\n  brep.Transform(Transform.Translation({-x}, {-y}, {-z}));\n"
        + anchor,
    )


def measure(path, task):
    from experiments.runner import sha256

    before = sha256(path)
    result = json.loads(script(measurement_code(path, task)))
    if sha256(path) != before:
        raise RuntimeError("Strip artifact changed during measurement")
    return result


def evaluate(task, measured):
    from experiments.strip_probe import evaluate as strip_checks
    from experiments.evaluator import near

    report = strip_checks(measured)
    objects = measured["objects"]
    one = objects[0] if len(objects) == 1 else {}
    checks = report["checks"]
    checks["volume"] = near(
        one.get("volume"), 10000 * math.pi, task["volume_tolerance"]
    )
    checks["area"] = near(one.get("area"), 3000 * math.pi + 400, task["area_tolerance"])
    bounds = one.get("min", []) + one.get("max", [])
    checks["bounds"] = len(bounds) == 6 and all(
        near(a, b, task["linear_tolerance"])
        for a, b in zip(bounds, [0, 0, 0, 110, 110, 10])
    )
    report["status"] = "pass" if all(checks.values()) else "fail"
    return report
