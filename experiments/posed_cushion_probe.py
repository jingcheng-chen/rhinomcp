"""Pose-sensitive cushion measurements using the unchanged local body predicates."""

import json
import math
from experiments.bridge import script
from experiments.runner import ROOT, sha256
from experiments.cushion_body_probe import samples, evaluate as evaluate_body
from experiments.cushion_probe import height

POSES = {"reclined": (65, [200, -40, 80]), "alternate": (-35, [-120, 70, 20])}


def inverse_code(pose):
    degrees, translation = POSES[pose]
    return f"Transform.Rotation({-math.radians(degrees):.17g},Vector3d.XAxis,Point3d.Origin)*Transform.Translation({-translation[0]},{-translation[1]},{-translation[2]})"


def forward_code(pose):
    degrees, translation = POSES[pose]
    return f"Transform.Translation({translation[0]},{translation[1]},{translation[2]})*Transform.Rotation({math.radians(degrees):.17g},Vector3d.XAxis,Point3d.Origin)"


def measure(path, pose="reclined"):
    scale = 1.0
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
    code = code.replace("o.Geometry", "localGeometry").replace(
        "foreach(var o in file.Objects) {",
        "foreach(var o in file.Objects) { var localGeometry=o.Geometry.Duplicate(); localGeometry.Transform("
        + inverse_code(pose)
        + ");",
    )
    result = json.loads(script(code))
    if before != sha256(path):
        raise RuntimeError("Artifact changed during read")
    return result


def evaluate(measured, pose="reclined"):
    if pose not in POSES:
        raise ValueError("Unknown pose")
    result = evaluate_body(measured)
    result["pose"] = pose
    result["limitation"] = (
        "Pose checked by inverse transform against the fixed local geometry and membership samples; no visual likeness score."
    )
    return result
