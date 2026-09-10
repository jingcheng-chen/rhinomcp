import copy

import pytest

from experiments.scene_task import same_edges, validate
from experiments.runner import ROOT, load_task


def test_edge_matching_accepts_reversed_and_cyclic_closed_curves():
    points = [[0, 0, 0], [3, 0, 0], [3, 2, 0], [0, 0, 0]]
    assert same_edges(points[::-1], points, 0.01)
    assert same_edges(points[1:] + [points[1]], points, 0.01)


@pytest.mark.parametrize(
    "actual",
    [
        [[0, 0, 0], [3, 0, 0]],  # missing segment
        [[0, 0, 0], [3, 2, 0], [3, 0, 0]],  # wrong connectivity
        [[0, 0, 0], [3, 0, 0], [0, 0, 0]],  # duplicate edge
        [[0, 0, 0], [3, 0, 0], [3, 2, 1]],  # wrong spatial endpoint
        [[0.009, 0.009, 0], [3, 0, 0], [3, 2, 0]],  # distance > tolerance
        [[0, 0], [3, 0, 0], [3, 2, 0]],
    ],
)
def test_edge_matching_rejects_missing_duplicate_bridge_and_bad_endpoints(actual):
    assert not same_edges(actual, [[0, 0, 0], [3, 0, 0], [3, 2, 0]], 0.01)


@pytest.mark.parametrize(
    "fault", ["nan", "bounds", "missing", "zero_segment", "point_count"]
)
def test_explicit_geometry_contract_rejects_ambiguous_inputs(fault):
    task = copy.deepcopy(load_task(ROOT / "experiments/tasks/join_two_components.json"))
    p = task["targets"][0]
    if fault == "nan":
        p["points"][0][0] = float("nan")
    elif fault == "bounds":
        p["max"][0] += 1
    elif fault == "missing":
        p.pop("points")
    elif fault == "zero_segment":
        p["points"][1] = p["points"][0]
    else:
        p["shape"] = "point"
    with pytest.raises(ValueError):
        validate(task)
