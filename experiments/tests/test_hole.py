import copy
import json
import math

import jsonschema
import pytest

from experiments.evaluator import evaluate
from experiments.runner import ROOT, load_task

TASK = load_task(ROOT / "experiments/tasks/through_hole.json")


def observation():
    planes = []
    for axis, size in enumerate((100, 60, 20)):
        for value in (0, size):
            origin, normal = [0, 0, 0], [0, 0, 0]
            origin[axis], normal[axis] = value, 1
            planes.append({"kind": "plane", "origin": origin, "normal": normal})
    wall = {
        "kind": "cylinder",
        "radius": 6,
        "center": [30, 20, 0],
        "axis": [0, 0, 1],
        "z_range": [0, 20],
        "axis_probe_ok": True,
        "axis_hits": 0,
        "axis_overlaps": 0,
    }
    return {
        "units": "Millimeters",
        "objects": [
            {
                "valid": True,
                "solid": True,
                "minimum": [0, 0, 0],
                "dimensions": [100, 60, 20],
                "volume": 120000 - 720 * math.pi,
                "area": 18400 + 168 * math.pi,
                "faces": planes + [wall],
            }
        ],
    }


def test_correct_hole():
    assert evaluate(TASK, observation())["status"] == "pass"


@pytest.mark.parametrize(
    "change,check",
    [
        ({"center": [35, 20, 0]}, "hole_axis"),
        ({"axis": [0, 1, 0]}, "hole_axis"),
        ({"radius": 7}, "hole_radius"),
        ({"z_range": [5, 20]}, "hole_full_height"),
        ({"axis_hits": 2}, "hole_axis_clear"),
        ({"axis_overlaps": 1}, "hole_axis_clear"),
        ({"axis_probe_ok": False}, "hole_axis_clear"),
    ],
)
def test_volume_cannot_hide_incorrect_hole(change, check):
    data = observation()
    data["objects"][0]["faces"][-1].update(change)
    report = evaluate(TASK, data)
    assert report["checks"]["volume"] is True
    assert report["checks"][check] is False
    assert report["status"] == "fail"


def test_rejects_interior_floor():
    data = observation()
    data["objects"][0]["faces"].append(
        {"kind": "plane", "origin": [30, 20, 5], "normal": [0, 0, 1]}
    )
    assert evaluate(TASK, data)["checks"]["outer_boundary_planes"] is False


def test_rejects_unrecognized_surface():
    data = observation()
    data["objects"][0]["faces"].append({"kind": "unsupported"})
    assert evaluate(TASK, data)["status"] == "fail"


@pytest.mark.parametrize("gap,expected", [(0, "pass"), (1, "fail")])
def test_cylindrical_face_subdivisions(gap, expected):
    data = observation()
    wall = data["objects"][0]["faces"][-1]
    other = copy.deepcopy(wall)
    wall["z_range"] = [0, 10]
    other["z_range"] = [10 + gap, 20]
    data["objects"][0]["faces"].append(other)
    assert evaluate(TASK, data)["status"] == expected


@pytest.mark.parametrize(
    "change",
    [
        {"hole_center": [0, 20]},
        {"hole_radius": 100},
        {"hole_radius": -1},
        {"hole_radius": float("nan")},
        {"hole_center": [30, float("inf")]},
        {"rotation_z_degrees": 30},
    ],
)
def test_rejects_invalid_task_before_rhino(tmp_path, change):
    path = tmp_path / "task.json"
    path.write_text(json.dumps({**TASK, **change}))
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        load_task(path)
