import math
import copy

import pytest
from experiments.strip_probe import evaluate, EXPECTED_MEMBERSHIP


def correct():
    return {
        "units": "Millimeters",
        "objects": [
            {
                "valid": True,
                "solid": True,
                "naked_edges": 0,
                "volume": 10000 * math.pi,
                "area": 3000 * math.pi + 400,
                "min": [0, 0, 0],
                "max": [110, 110, 10],
                "membership": EXPECTED_MEMBERSHIP.copy(),
            }
        ],
    }


def test_exact_strip_passes():
    assert evaluate(correct())["status"] == "pass"


@pytest.mark.parametrize(
    "change",
    [
        {"solid": False, "naked_edges": 8, "volume": None},
        {"min": [5, 0, 0]},
        {"max": [130, 130, 8.333333]},
        {"volume": float("nan")},
        {"area": 0},
        {"membership": [False] * len(EXPECTED_MEMBERSHIP)},
    ],
)
def test_defects_cannot_pass_on_volume_alone(change):
    data = correct()
    data["objects"][0].update(change)
    assert evaluate(data)["status"] == "fail"


def test_extra_geometry_and_wrong_units_fail():
    data = correct()
    data["objects"].append(copy.deepcopy(data["objects"][0]))
    assert not evaluate(data)["checks"]["one_object"]
    data = correct()
    data["units"] = "Inches"
    assert not evaluate(data)["checks"]["millimeters"]
