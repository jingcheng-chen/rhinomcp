from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments import campaign as c
from experiments.trial import persist, read


@pytest.fixture
def queue(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    monkeypatch.setattr(c.comparison, "check_pins", lambda p: None)
    monkeypatch.setattr(c, "handoff", lambda previous, child: None)
    runs = tmp_path / "experiments/runs"
    runs.mkdir(parents=True)
    paths = []
    for i in range(3):
        child = runs / str(i)
        child.mkdir()
        persist(
            child / "contract.json",
            {
                "evaluation_mode": "trusted_baseline",
                "binaries": {"baseline": {"identity": "baseline"}},
                "agent": "fixed",
                "acceptance": "correctness_then_calls_v1",
            },
        )
        persist(child / "suite.json", {"tasks": [{"family": "solid", "path": "box"}]})
        persist(
            child / "state.json",
            {"stage": "prepared", "rows": [], "runtime_dirty": False},
        )
        persist(
            child / "resources.json",
            {
                "limits": {"sessions": 4, "tool_attempts": 40, "model_seconds": 200},
                "pending": None,
                "completed": [],
                "used": {"sessions": 0, "tool_attempts": 0, "model_seconds": 0},
                "stopped": False,
            },
        )
        persist(
            child / "schedule.json", c.comparison.schedule(read(child / "suite.json"))
        )
        paths.append(child)
    return paths


def prepare(queue, **kwargs):
    return c.prepare(
        queue,
        kwargs.get(
            "limits", {"sessions": 12, "tool_attempts": 120, "model_seconds": 600}
        ),
        kwargs.get("max_no_benefit", 3),
        "Reviewed exact queue",
    )


def finish(child, benefit=False):
    plan = read(child / "schedule.json")
    rows = [
        {
            "id": s["name"],
            "task": s["entry"]["path"],
            "arm": s["arm"],
            "task_verdict": "pass",
            "metrics": {
                "mcp_attempts": 2 if benefit and s["arm"] == "candidate" else 3,
                "failed_calls": 0,
            },
            "elapsed_seconds": 10,
        }
        for s in plan
    ]
    state = read(child / "state.json")
    state.update(stage="complete", rows=rows)
    persist(child / "state.json", state)
    resources = read(child / "resources.json")
    resources["completed"] = [
        {
            "name": row["id"],
            "actual": {
                "sessions": 1,
                "tool_attempts": row["metrics"]["mcp_attempts"],
                "model_seconds": 10,
            },
        }
        for row in rows
    ]
    resources["used"] = {
        k: sum(e["actual"][k] for e in resources["completed"]) for k in c.budget.KEYS
    }
    persist(child / "resources.json", resources)
    persist(child / "comparison.json", c.comparison.summarize(rows, plan))


def test_queue_runs_in_order_stops_at_first_benefit_without_selecting(
    queue, monkeypatch
):
    directory = prepare(queue)
    seen = []

    def dispatch(command, **kwargs):
        child = Path(command[-1])
        seen.append(child)
        assert read(directory / "state.json")["active"] == len(seen) - 1
        finish(child, benefit=len(seen) == 2)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(c.subprocess, "run", dispatch)
    state = c.run(directory)
    assert seen == queue[:2]
    assert state["stage"] == "selection_review"
    assert state["used"]["sessions"] == 8
    assert c.run(directory) == state
    assert len(seen) == 2


def test_lost_parent_accounts_completed_child_without_replay(queue, monkeypatch):
    directory = prepare(queue)
    assert c.admit(directory) == queue[0]
    finish(queue[0], benefit=True)
    monkeypatch.setattr(c.subprocess, "run", lambda *a, **k: pytest.fail("replayed"))
    assert c.run(directory)["stage"] == "selection_review"


def test_uncertain_child_blocks_more_dispatch(queue):
    directory = prepare(queue)
    c.admit(directory)
    with pytest.raises(RuntimeError, match="Unaccounted"):
        c.admit(directory)
    with pytest.raises(RuntimeError, match="incomplete"):
        c.reconcile(directory)
    assert read(directory / "state.json")["active"] == 0


@pytest.mark.parametrize("kind", ["resource", "no_benefit", "exhausted"])
def test_finite_stop_conditions(queue, kind):
    directory = prepare(
        queue[:1] if kind == "exhausted" else queue,
        limits={"sessions": 4, "tool_attempts": 40, "model_seconds": 200}
        if kind == "resource"
        else {"sessions": 12, "tool_attempts": 120, "model_seconds": 600},
        max_no_benefit=1 if kind == "no_benefit" else 3,
    )
    child = c.admit(directory)
    finish(child)
    c.reconcile(directory)
    assert c.admit(directory) is None
    assert (
        read(directory / "state.json")["stage"]
        == {
            "resource": "resource_stop",
            "no_benefit": "no_benefit_stop",
            "exhausted": "exhausted",
        }[kind]
    )


def test_bad_ledger_or_changed_evidence_cannot_be_accounted(queue):
    directory = prepare(queue)
    child = c.admit(directory)
    finish(child)
    resources = read(child / "resources.json")
    resources["used"]["tool_attempts"] = 0
    persist(child / "resources.json", resources)
    with pytest.raises(RuntimeError, match="account"):
        c.reconcile(directory)
    finish(child)
    c.reconcile(directory)
    persist(child / "comparison.json", {})
    with pytest.raises(RuntimeError, match="evidence changed"):
        c.admit(directory)


def test_mismatched_baseline_rejected_before_campaign_creation(queue):
    contract = read(queue[1] / "contract.json")
    contract["binaries"]["baseline"]["identity"] = "different"
    persist(queue[1] / "contract.json", contract)
    with pytest.raises(ValueError, match="share baseline"):
        prepare(queue)


def test_failure_stops_queue_and_retains_active_child(queue, monkeypatch):
    directory = prepare(queue)
    monkeypatch.setattr(
        c.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1)
    )
    with pytest.raises(RuntimeError, match="dispatch stopped"):
        c.run(directory)
    assert read(directory / "state.json")["active"] == 0
    assert read(directory / "failure.json")["directory"] == str(queue[0])


def test_handoff_only_transfers_verified_previous_document(tmp_path, monkeypatch):
    from experiments import rhino_trial, strip_probe

    monkeypatch.setattr(c, "ROOT", tmp_path)
    (tmp_path / "experiments/runs").mkdir(parents=True)
    previous, child = tmp_path / "previous", tmp_path / "child"
    previous.mkdir()
    child.mkdir()
    (previous / "last").mkdir()
    binary = tmp_path / "binary"
    binary.write_bytes(b"reviewed")
    expected = {"mvid": "old", "sha256": c.sha256(binary)}
    monkeypatch.setattr(c, "common", lambda p: {"baseline": expected})
    owner = {"pid": 10, "document": 20}
    current = {
        **owner,
        "docs": [{}],
        "path": None,
        "object_count": 0,
        "marker": None,
        "assembly": str(binary),
        "mvid": "old",
    }
    monkeypatch.setattr(rhino_trial, "runtime", lambda: current)
    monkeypatch.setattr(strip_probe, "fingerprint", lambda: {"preserved": True})
    persist(
        previous / "state.json",
        {"stage": "complete", "runtime_dirty": False, "rows": [{"id": "last"}]},
    )
    persist(previous / "runtime-owner.json", owner)
    persist(previous / "last/preservation.json", {"after": {"preserved": True}})
    c.handoff(previous, child)
    assert read(child / "runtime-owner.json") == owner
    current["pid"] = 99
    with pytest.raises(RuntimeError, match="not owned"):
        c.handoff(previous, child)
    current["pid"] = 10
    current["object_count"] = 1
    with pytest.raises(RuntimeError, match="empty owned"):
        c.handoff(previous, child)
    current["object_count"] = 0
    monkeypatch.setattr(strip_probe, "fingerprint", lambda: {"preserved": False})
    with pytest.raises(RuntimeError, match="Document changed"):
        c.handoff(previous, child)
