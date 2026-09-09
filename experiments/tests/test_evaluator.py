import copy
import json
from pathlib import Path

import pytest
from experiments.evaluator import evaluate

TASK = json.loads((Path(__file__).parents[1] / "tasks/box.json").read_text())
CORRECT = {
    "units": "Millimeters",
    "objects": [
        {
            "valid": True,
            "solid": True,
            "minimum": [0, 0, 0],
            "dimensions": [100, 50, 30],
            "volume": 150000,
        }
    ],
}


def test_correct():
    assert evaluate(TASK, CORRECT)["status"] == "pass"


@pytest.mark.parametrize(
    "key,value",
    [
        ("valid", False),
        ("solid", False),
        ("minimum", [1, 0, 0]),
        ("dimensions", [100, 30, 50]),
        ("volume", 149000),
        ("volume", None),
        ("volume", float("nan")),
        ("dimensions", [100]),
        ("dimensions", [float("inf"), 50, 30]),
    ],
)
def test_rejects_wrong_geometry(key, value):
    observed = copy.deepcopy(CORRECT)
    observed["objects"][0][key] = value
    assert evaluate(TASK, observed)["status"] == "fail"


@pytest.mark.parametrize("count", [0, 2])
def test_checks_entire_output(count):
    observed = copy.deepcopy(CORRECT)
    observed["objects"] *= count
    assert evaluate(TASK, observed)["status"] == "fail"


def test_units():
    assert evaluate(TASK, {**CORRECT, "units": "Meters"})["status"] == "fail"
