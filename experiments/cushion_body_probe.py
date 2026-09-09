"""Closed-body checks plus the unchanged top judge in normalized coordinates."""

import copy
import json
import math
from experiments.bridge import script
from experiments.cushion_probe import height, evaluate as evaluate_top
from experiments.runner import ROOT, sha256


def scale_value(scale):
    if scale not in (1.0, 0.75):
        raise ValueError("Supported scales are 1 and 0.75")
    return scale


def samples():
    return [
        (x, y, z)
        for x in [-2, 10, 25, 50, 75, 90, 102]
        for y in [-2, 10, 25, 50, 75, 90, 102]
        for z in [-2, 2, 8, 15, 24, 32]
        if abs(z - height(x, y)) > 2
    ]


def measure(path, scale=1.0):
    scale_value(scale)
    before = sha256(path)

    def point(x, y, z):
        return f"new Point3d({x * scale:.15g},{y * scale:.15g},{z * scale:.15g})"

    code = (
        (ROOT / "experiments/cushion_body_measure.cs")
        .read_text()
        .replace("ARTIFACT_PATH", json.dumps(str(path)))
        .replace("SCALE_VALUE", str(scale))
        .replace(
            "EXPECTED_POINTS",
            ",".join(
                point(x, y, height(x, y))
                for x in range(0, 101, 5)
                for y in range(0, 101, 5)
            ),
        )
        .replace("MEMBERSHIP_POINTS", ",".join(point(*p) for p in samples()))
    )
    result = json.loads(script(code))
    if before != sha256(path):
        raise RuntimeError("Artifact changed during read")
    return result


def evaluate(measured, scale=1.0):
    scale_value(scale)
    data = copy.deepcopy(measured)
    for layer in data["layers"]:
        if layer["name"] == "Body":
            layer["name"] = "Top"
    for obj in data["objects"]:
        obj["name"] = "cushion_top" if obj["name"] == "cushion_body" else obj["name"]
        obj["faces"] = 1 if obj["nonplanar"] == 1 else 0
        obj["solid"] = False  # The reused top judge evaluates the extracted top face.
        for key in ["min", "max", "distances"]:
            obj[key] = [v / scale for v in obj[key]]
        obj["points"] = [[v / scale for v in p] for p in obj["points"]]
    top = evaluate_top(data)
    obj = measured["objects"][0] if len(measured["objects"]) == 1 else {}
    checks = top["checks"]
    volume = obj.get("volume")
    expected_volume = 10000 * (10 + 20 * (18 / 35) ** 2) * scale**3
    checks.update(
        closed_solid=obj.get("solid") is True,
        zero_naked_edges=obj.get("naked_edges") == 0,
        planar_boundary=obj.get("boundaryPlanes") is True,
        bottom_at_zero=obj.get("hasBottom") is True,
        body_layer_name=any(layer["name"] == "Body" for layer in measured["layers"])
        and not any(layer["name"] == "Top" for layer in measured["layers"]),
        volume=isinstance(volume, (int, float))
        and math.isfinite(volume)
        and abs(volume - expected_volume) <= expected_volume * 0.01,
        membership=obj.get("membership")
        == [
            0 < x < 100 and 0 < y < 100 and 0 < z < height(x, y)
            for x, y, z in samples()
        ],
    )
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "scale": scale,
        "max_height_error_mm": None
        if top["max_height_error_mm"] is None
        else top["max_height_error_mm"] * scale,
        "expected_volume": expected_volume,
        "measurements": measured,
    }
