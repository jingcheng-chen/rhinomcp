import copy

import pytest

from experiments.layer_probe import ZERO, evaluate


def correct():
    layers = []
    for index, (name, parent) in enumerate(
        (
            ("Assembly", ZERO),
            ("Left", "0"),
            ("Right", "0"),
            ("Part", "1"),
            ("Part", "2"),
        )
    ):
        layers.append(
            dict(
                id=str(index),
                index=index,
                name=name,
                parent=parent,
                visible=True,
                locked=False,
            )
        )
    objects = [
        dict(
            name=name,
            layer=3 + i,
            visible=True,
            mode="Normal",
            valid=True,
            solid=True,
            min=[i * 30, 0, 0],
            max=[i * 30 + 10, 10, 10],
        )
        for i, name in enumerate(("left_part", "right_part"))
    ]
    return dict(units="Millimeters", layers=layers, objects=objects)


def test_duplicate_leaf_names_with_distinct_parents_pass():
    assert evaluate(correct())["status"] == "pass"


@pytest.mark.parametrize(
    "fault",
    [
        "cycle",
        "missing_parent",
        "duplicate_id",
        "wrong_parent",
        "hidden_parent",
        "locked_child",
        "wrong_assignment",
        "extra_object",
        "wrong_geometry",
        "hidden_object",
        "wrong_units",
    ],
)
def test_layer_judge_rejects_structural_and_geometry_faults(fault):
    m = correct()
    if fault == "cycle":
        m["layers"][0]["parent"] = "3"
    elif fault == "missing_parent":
        m["layers"][1]["parent"] = "absent"
    elif fault == "duplicate_id":
        m["layers"][4]["id"] = "3"
    elif fault == "wrong_parent":
        m["layers"][2]["parent"] = "1"
    elif fault == "hidden_parent":
        m["layers"][0]["visible"] = False
    elif fault == "locked_child":
        m["layers"][4]["locked"] = True
    elif fault == "wrong_assignment":
        m["objects"][1]["layer"] = 3
    elif fault == "extra_object":
        m["objects"].append(copy.deepcopy(m["objects"][0]))
    elif fault == "wrong_geometry":
        m["objects"][1]["max"][0] = 39
    elif fault == "hidden_object":
        m["objects"][1]["visible"] = False
    else:
        m["units"] = "Inches"
    assert evaluate(m)["status"] == "fail"
