import copy
import json
import math

import pytest
import jsonschema

from experiments.evaluator import evaluate
from experiments.runner import ROOT, load_task

TASK = load_task(ROOT / "experiments/tasks/posed_prism.json")


def observation(angle=30, translation=(120, -40, 15)):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    vertices = [
        [
            c * x - s * y + translation[0],
            s * x + c * y + translation[1],
            z + translation[2],
        ]
        for z in (0, 25)
        for x, y in ((0, 0), (80, 0), (0, 40))
    ]
    return {
        "units": "Millimeters",
        "objects": [
            {
                "valid": True,
                "solid": True,
                "vertices": vertices,
                "planar_faces": True,
                "straight_edges": True,
                "volume": 40000,
                "area": 3200 + 25 * (120 + math.hypot(80, 40)),
            }
        ],
    }


def test_correct_pose():
    assert evaluate(TASK, observation())["status"] == "pass"


@pytest.mark.parametrize(
    "angle,translation",
    [(-30, (120, -40, 15)), (0, (120, -40, 15)), (30, (121, -40, 15))],
)
def test_same_volume_does_not_hide_wrong_pose(angle, translation):
    report = evaluate(TASK, observation(angle, translation))
    assert report["checks"]["volume"] is True
    assert report["checks"]["pose_corners"] is False
    assert report["status"] == "fail"


def test_allows_equivalent_split_faces():
    data = observation()
    vertices = data["objects"][0]["vertices"]
    vertices.append([(a + b) / 2 for a, b in zip(vertices[0], vertices[1])])
    assert evaluate(TASK, data)["status"] == "pass"


def test_rejects_protrusion_even_when_corners_and_volume_match():
    data = observation()
    data["objects"][0]["vertices"].append([1000, 1000, 1000])
    report = evaluate(TASK, data)
    assert report["checks"]["pose_corners"] is True
    assert report["checks"]["vertices_inside"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("planar_faces", False),
        ("straight_edges", False),
        ("area", 0),
        ("volume", None),
        ("vertices", []),
    ],
)
def test_rejects_invalid_shape(field, value):
    data = observation()
    data["objects"][0][field] = value
    assert evaluate(TASK, data)["status"] == "fail"


@pytest.mark.parametrize(
    "change",
    [
        {"type": "unknown"},
        {"minimum": [0, 0, 0]},
        {"rotation_z_degrees": float("inf")},
        {"dimensions": [80, 0, 25]},
    ],
)
def test_rejects_invalid_task_contract(tmp_path, change):
    task = copy.deepcopy(TASK)
    task.update(change)
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task))
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        load_task(path)
