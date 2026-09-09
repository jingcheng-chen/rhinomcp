"""Fixed cushion-top judge: continuity, bidirectional sampling and saved layers."""

import json
import math

from experiments.bridge import script
from experiments.layer_probe import ZERO
from experiments.runner import ROOT, sha256


def height(x, y):
    def f(t):
        return 432 * t**2 * (t - 0.5) ** 2 * (t - 1) ** 2

    return 10 + 20 * f(x / 100) * f(y / 100)


def measure(path):
    before = sha256(path)
    points = ",".join(
        f"new Point3d({x},{y},{height(x, y):.15g})"
        for x in range(0, 101, 5)
        for y in range(0, 101, 5)
    )
    code = (ROOT / "experiments/cushion_measure.cs").read_text()
    result = json.loads(
        script(
            code.replace("ARTIFACT_PATH", json.dumps(str(path))).replace(
                "EXPECTED_POINTS", points
            )
        )
    )
    if sha256(path) != before:
        raise RuntimeError("Artifact changed during measurement")
    return result


def evaluate(measured):
    layers = measured["layers"]
    by_id = {layer["id"]: layer for layer in layers}

    def path(layer, seen=()):
        if layer["id"] in seen:
            raise ValueError("Layer cycle")
        return (
            layer["name"]
            if layer["parent"] == ZERO
            else path(by_id[layer["parent"]], (*seen, layer["id"]))
            + "::"
            + layer["name"]
        )

    try:
        paths = {layer["index"]: path(layer) for layer in layers}
        tree = len(by_id) == len(layers) == len(paths) == len(
            set(paths.values())
        ) and set(paths.values()) - {"Default"} == {
            "Cushion",
            "Cushion::Upholstery",
            "Cushion::Upholstery::Top",
        }
    except (ValueError, KeyError):
        paths, tree = {}, False
    objects = measured["objects"]
    obj = objects[0] if len(objects) == 1 else {}
    points, distances = obj.get("points", []), obj.get("distances", [])
    finite_points = len(points) == 1681 and all(
        len(p) == 3 and all(isinstance(a, (int, float)) and math.isfinite(a) for a in p)
        for p in points
    )
    errors = [abs(p[2] - height(p[0], p[1])) for p in points] if finite_points else []
    bounds = obj.get("min", []) + obj.get("max", [])
    checks = {
        "millimeters": measured["units"] == "Millimeters",
        "one_named_surface": len(objects) == 1 and obj.get("name") == "cushion_top",
        "layer_tree": tree,
        "layer_assignment": paths.get(obj.get("layer")) == "Cushion::Upholstery::Top",
        "visible_unlocked": obj.get("visible") is True
        and obj.get("mode") == "Normal"
        and all(layer["visible"] and not layer["locked"] for layer in layers),
        "valid_single_untrimmed_open_face": obj.get("valid") is True
        and obj.get("faces") == 1
        and obj.get("untrimmed") is True
        and obj.get("solid") is False,
        "smooth_first_derivatives": obj.get("smooth") is True,
        "xy_bounds": len(bounds) == 6
        and all(
            isinstance(bounds[i], (int, float))
            and math.isfinite(bounds[i])
            and abs(bounds[i] - v) <= 0.01
            for i, v in [(0, 0), (1, 0), (3, 100), (4, 100)]
        ),
        "surface_to_target": finite_points
        and max(errors) <= 1
        and all(-0.01 <= p[0] <= 100.01 and -0.01 <= p[1] <= 100.01 for p in points),
        "target_coverage": len(distances) == 441
        and all(
            isinstance(d, (int, float)) and math.isfinite(d) and 0 <= d <= 1
            for d in distances
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "max_height_error_mm": max(errors) if errors else None,
        "max_target_distance_mm": max(distances) if distances else None,
        "measurements": measured,
    }
