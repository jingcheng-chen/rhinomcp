import copy
import json

import pytest
from jsonschema import ValidationError

from experiments.assembly_task import load
from experiments.runner import ROOT
from experiments.layer_probe import evaluate, ZERO


def task():
    return load(ROOT / "experiments/assembly_tasks/deep_stand.json")


def correct():
    spec = task()
    indices = {path: i for i, path in enumerate(spec["layers"])}
    layers = [
        dict(
            id=str(i),
            index=i,
            name=path.split("::")[-1],
            parent=str(indices[path.rsplit("::", 1)[0]]) if "::" in path else ZERO,
            visible=True,
            locked=False,
        )
        for path, i in indices.items()
    ]
    objects = [
        dict(
            name=p["name"],
            layer=indices[p["layer"]],
            min=p["min"],
            max=p["max"],
            visible=True,
            mode="Normal",
            valid=True,
            solid=True,
        )
        for p in spec["parts"]
    ]
    return dict(units="Millimeters", layers=layers, objects=objects)


def test_repeated_intermediate_names_and_distinct_bounds_pass():
    assert evaluate(correct(), task=task())["status"] == "pass"


@pytest.mark.parametrize(
    "fault", ["ancestor", "part_layer", "duplicate_name", "nan", "reversed_bounds"]
)
def test_invalid_task_rejected(tmp_path, fault):
    spec = copy.deepcopy(task())
    if fault == "ancestor":
        spec["layers"].remove("Stand::Right::Support")
    elif fault == "part_layer":
        spec["parts"][0]["layer"] = "Stand::Missing"
    elif fault == "duplicate_name":
        spec["parts"][1]["name"] = spec["parts"][0]["name"]
    elif fault == "nan":
        spec["parts"][0]["max"][0] = float("nan")
    else:
        spec["parts"][0]["max"][0] = -1
    path = tmp_path / "task.json"
    path.write_text(json.dumps(spec))
    with pytest.raises((ValueError, ValidationError)):
        load(path)


@pytest.mark.parametrize("fault", ["branch_swap", "hidden_intermediate"])
def test_deeper_structure_faults_are_rejected(fault):
    measured = correct()
    if fault == "branch_swap":
        measured["objects"][1]["layer"] = measured["objects"][0]["layer"]
    else:
        measured["layers"][5]["visible"] = False
    assert evaluate(measured, task=task())["status"] == "fail"
