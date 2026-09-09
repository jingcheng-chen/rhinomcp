import copy
import json
import math

import pytest

from experiments.runner import ROOT
from experiments.trimmed_task import evaluate, measurement_code


def task():
    return json.loads((ROOT / "experiments/tasks/trimmed_offset.json").read_text())


def measured():
    return {
        "units": "Millimeters",
        "objects": [
            {
                "valid": True,
                "faces": 1,
                "solid": False,
                "planar": True,
                "outer_loops": 1,
                "inner_loops": 1,
                "min": [0, 0, 0],
                "max": [100, 80, 0],
                "outer_error": 0,
                "inner_error": 0,
                "area": 8000 - math.pi * 144,
                "membership_errors": 0,
                "membership_samples": 1600,
            }
        ],
    }


def test_independent_analytic_trimmed_patch():
    assert evaluate(task(), measured())["status"] == "pass"


@pytest.mark.parametrize(
    "field,value",
    [
        ("valid", False),
        ("faces", 2),
        ("solid", True),
        ("planar", False),
        ("inner_loops", 0),
        ("outer_loops", 2),
        ("inner_error", 1),
        ("outer_error", 1),
        ("area", 8000),
        ("membership_errors", 1),
        ("membership_samples", 0),
        ("max", [101, 80, 0]),
    ],
)
def test_each_required_predicate_can_reject(field, value):
    data = measured()
    data["objects"][0][field] = value
    assert evaluate(task(), data)["status"] == "fail"


def test_hidden_extras_missing_and_nonfinite_measurements_reject():
    data = measured()
    data["objects"].append(copy.deepcopy(data["objects"][0]))
    assert evaluate(task(), data)["status"] == "fail"
    assert evaluate(task(), {})["status"] == "fail"
    data = measured()
    data["objects"][0]["area"] = float("nan")
    assert evaluate(task(), data)["status"] == "fail"


def test_measurement_template_contains_only_explicit_task_pose(tmp_path):
    code = measurement_code(tmp_path / "model.3dm", task())
    assert "ARTIFACT_PATH" not in code and "VALUE" not in code
    assert "DuplicateBrep" in code and "File3dm.Read" in code
