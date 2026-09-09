import copy
import json
import pytest
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
