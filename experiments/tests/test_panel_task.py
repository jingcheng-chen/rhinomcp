import copy
import json
import pytest
import jsonschema
from experiments.runner import ROOT, load_task
from experiments.panel_task import evaluate
from experiments.workflow.pilot import load_suite


def valid():
    return {
        "units": "Millimeters",
        "objects": [
            {
                "valid": True,
                "solid": False,
                "faces": 1,
                "outer_loops": 1,
                "inner_loops": 0,
                "min": [0, 0, 0],
                "max": [100, 80, 20],
                "reference_error": 0,
                "surface_error": 0,
                "boundary_error": 0,
            }
        ],
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("valid", False),
        ("solid", True),
        ("faces", 2),
        ("inner_loops", 1),
        ("reference_error", 1),
        ("surface_error", 1),
        ("boundary_error", 1),
        ("reference_error", float("nan")),
        ("max", [100, 80, 0]),
    ],
)
def test_panel_rejects_geometry_failures(key, value):
    task = load_task(ROOT / "experiments/tasks/panel_raised.json")
    m = valid()
    assert evaluate(task, m)["status"] == "pass"
    m["objects"][0][key] = value
    assert evaluate(task, m)["status"] == "fail"


def test_panel_counts_all_objects_and_units():
    task = load_task(ROOT / "experiments/tasks/panel_raised.json")
    m = valid()
    m["objects"].append({"valid": False})
    assert evaluate(task, m)["status"] == "fail"
    m = valid()
    m["units"] = "Meters"
    assert evaluate(task, m)["status"] == "fail"


def test_panel_registration_and_finite_parameters(tmp_path):
    suite = load_suite(ROOT / "experiments/workflow/panel-pilot.json")
    assert {e["family"] for e in suite["tasks"]} == {"curved-panels"}
    task = load_task(ROOT / "experiments/tasks/panel_depressed.json")
    for key in ["panel_height", "rotation_x_degrees"]:
        changed = copy.deepcopy(task)
        changed[key] = float("nan")
        p = tmp_path / "task.json"
        p.write_text(json.dumps(changed))
        with pytest.raises(ValueError):
            load_task(p)


def test_v2_shape_budget_does_not_relax_boundary_pose_or_topology():
    task = load_task(ROOT / "experiments/tasks/panel_raised_v2.json")
    data = valid()
    data["objects"][0]["reference_error"] = 0.4
    data["objects"][0]["surface_error"] = 0.4
    assert evaluate(task, data)["status"] == "pass"
    # Historical task retains its original verdict for identical measurements.
    old = load_task(ROOT / "experiments/tasks/panel_raised.json")
    assert evaluate(old, data)["status"] == "fail"
    for key, value in [
        ("boundary_error", 0.01),
        ("min", [0.01, 0, 0]),
        ("inner_loops", 1),
        ("surface_error", 0.51),
    ]:
        changed = copy.deepcopy(data)
        changed["objects"][0][key] = value
        assert evaluate(task, changed)["status"] == "fail"


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_shape_tolerance_requires_positive_finite_value(tmp_path, value):
    task = load_task(ROOT / "experiments/tasks/panel_raised_v2.json")
    task["shape_tolerance"] = value
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task))
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        load_task(path)


def test_shape_tolerance_is_not_accepted_for_analytic_solids(tmp_path):
    task = load_task(ROOT / "experiments/tasks/box.json")
    task["shape_tolerance"] = 0.5
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task))
    with pytest.raises(jsonschema.ValidationError):
        load_task(path)
