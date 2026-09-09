import pytest
from experiments.workflow import budget
from experiments.trial import read


def setup(tmp_path):
    path = tmp_path / "resources.json"
    budget.initialize(path, dict(sessions=2, tool_attempts=20, model_seconds=100))
    return path


def test_interrupted_reservation_cannot_dispatch_or_initialize_again(tmp_path):
    path = setup(tmp_path)
    allowance = dict(sessions=1, tool_attempts=10, model_seconds=50)
    budget.reserve(path, "first", allowance)
    with pytest.raises(RuntimeError, match="Unaccounted"):
        budget.reserve(path, "next", allowance)
    with pytest.raises(ValueError, match="already exists"):
        budget.initialize(path, allowance)
    assert read(path)["pending"]["name"] == "first"


def test_actual_usage_is_retained_and_overshoot_stops_new_work(tmp_path):
    path = setup(tmp_path)
    allowance = dict(sessions=1, tool_attempts=10, model_seconds=50)
    budget.reserve(path, "first", allowance)
    state = budget.settle(
        path, "first", dict(sessions=1, tool_attempts=21, model_seconds=45)
    )
    assert state["used"]["tool_attempts"] == 21
    assert state["stopped"]
    with pytest.raises(RuntimeError, match="limit"):
        budget.reserve(path, "next", allowance)


def test_settlement_requires_matching_dispatch_and_prevents_replay(tmp_path):
    path = setup(tmp_path)
    allowance = dict(sessions=1, tool_attempts=10, model_seconds=50)
    budget.reserve(path, "first", allowance)
    with pytest.raises(RuntimeError, match="matching"):
        budget.settle(path, "other", allowance)
    budget.settle(path, "first", allowance)
    with pytest.raises(RuntimeError, match="replayed"):
        budget.reserve(path, "first", allowance)
    with pytest.raises(RuntimeError, match="matching"):
        budget.settle(path, "first", allowance)
    budget.reserve(path, "second", allowance)
    budget.settle(path, "second", allowance)
    with pytest.raises(RuntimeError, match="limit"):
        budget.reserve(path, "third", allowance)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, None])
def test_invalid_resource_counts_cannot_disable_limits(value):
    with pytest.raises(ValueError):
        budget.amounts(dict(sessions=1, tool_attempts=value, model_seconds=10))
