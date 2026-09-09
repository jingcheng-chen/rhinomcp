"""Fault checks for completed-prefix continuation; no real Rhino or agents."""

import pytest

from experiments.trial import persist, read
from experiments.workflow import binary_compare as bc, budget


@pytest.fixture
def run_env(tmp_path, monkeypatch):
    monkeypatch.setattr(bc, "ROOT", tmp_path)
    (tmp_path / "experiments/runs").mkdir(parents=True)
    directory = tmp_path / "comparison"
    directory.mkdir()
    suite = {
        "tasks": [{"path": "task", "family": "solid"}],
        "call_budget": 10,
        "timeout_seconds": 30,
    }
    plan = bc.schedule(suite)
    contract = {
        "agent": {"model": "test", "reasoning_effort": "medium"},
        "evaluation_mode": "trusted_baseline",
    }
    for name, value in {
        "contract.json": contract,
        "suite.json": suite,
        "schedule.json": plan,
        "tools.json": [],
        "state.json": {"stage": "prepared", "runtime_dirty": False, "rows": []},
    }.items():
        persist(directory / name, value)
    budget.initialize(
        directory / "resources.json",
        {"sessions": 4, "tool_attempts": 44, "model_seconds": 160},
    )
    monkeypatch.setattr(bc, "check_pins", lambda d: None)
    ident = {"sha256": "binary", "mvid": "mvid"}
    monkeypatch.setattr(bc, "identity", lambda arm, d: ident)
    monkeypatch.setattr(bc.rhino_trial, "probe", lambda d: ident)
    environment = {"stable": True}
    monkeypatch.setattr(bc, "session_environment", lambda d: environment)
    dispatches = []
    judgments = []

    def recover(d):
        state = read(d / "state.json")
        state.update(stage="restored", runtime_dirty=False)
        persist(d / "state.json", state)

    monkeypatch.setattr(bc, "recover", recover)

    def task(child, *args, **kwargs):
        dispatches.append(child.name)
        child.mkdir()
        (child / "candidate.3dm").write_bytes(b"model")
        persist(child / "task.json", {"instruction": "unchanged"})
        persist(
            child / "artifact.json",
            {
                "sha256": bc.sha256(child / "candidate.3dm"),
                "task_sha256": bc.sha256(child / "task.json"),
                "evaluation_pending": True,
            },
        )
        persist(
            child / "environment.json",
            {"plugin_sha256": "binary", "rhino": {"mvid": "mvid"}},
        )

    monkeypatch.setattr(bc, "run_task", task)

    def audit(root, spec):
        return {
            "id": spec["id"],
            "task_verdict": "pass",
            "metrics": {"mcp_attempts": 2, "failed_calls": 0},
            "elapsed_seconds": 5,
        }

    monkeypatch.setattr(bc, "audit_run", audit)

    def evaluate(child, expected):
        judgments.append(child.name)
        persist(child / "evaluation.json", {"status": "pass"})

    monkeypatch.setattr(bc, "evaluate_saved", evaluate)
    return directory, plan, dispatches, judgments


def test_pause_resume_never_repeats_completed_session(run_env):
    directory, plan, dispatches, judgments = run_env
    bc.run(directory, max_sessions=1)
    assert read(directory / "state.json")["stage"] == "paused"
    assert dispatches == [plan[0]["name"]]
    assert judgments == []
    bc.run(directory, resume=True, max_sessions=1)
    assert len(dispatches) == 2
    bc.run(directory, resume=True)
    assert dispatches == [s["name"] for s in plan]
    assert judgments == dispatches
    assert read(directory / "resources.json")["used"] == {
        "sessions": 4,
        "tool_attempts": 8,
        "model_seconds": 20,
    }
    assert read(directory / "state.json")["stage"] == "complete"
    with pytest.raises(RuntimeError, match="Completed"):
        bc.run(directory, resume=True)
    assert len(dispatches) == 4


@pytest.mark.parametrize(
    "fault",
    [
        "model",
        "task",
        "ledger",
        "active",
        "uncheckpointed",
        "evaluation",
        "receipt",
        "rows",
    ],
)
def test_resume_refuses_uncertain_or_changed_evidence(run_env, fault):
    directory, plan, dispatches, _ = run_env
    bc.run(directory, max_sessions=1)
    child = directory / plan[0]["name"]
    if fault == "model":
        (child / "candidate.3dm").write_bytes(b"changed")
    elif fault == "task":
        persist(child / "task.json", {"instruction": "changed"})
    elif fault == "ledger":
        state = read(directory / "resources.json")
        state["pending"] = {"name": plan[1]["name"]}
        persist(directory / "resources.json", state)
    elif fault == "active":
        state = read(directory / "state.json")
        state["active_session"] = plan[1]["name"]
        persist(directory / "state.json", state)
    elif fault == "uncheckpointed":
        (directory / plan[1]["name"]).mkdir()
    elif fault == "evaluation":
        persist(child / "evaluation.json", {"status": "pass"})
    elif fault == "receipt":
        persist(directory / "checkpoints/modeling-1.json", {})
    else:
        state = read(directory / "state.json")
        state["rows"][0]["metrics"]["mcp_attempts"] = 0
        persist(directory / "state.json", state)
    with pytest.raises(RuntimeError):
        bc.run(directory, resume=True)
    assert len(dispatches) == 1


def test_process_loss_after_durable_checkpoint_can_continue(run_env):
    directory, plan, dispatches, _ = run_env
    bc.run(directory, max_sessions=1)
    state = read(directory / "state.json")
    state["stage"] = "running"  # Lost process before the clean pause write.
    persist(directory / "state.json", state)
    bc.run(directory, resume=True)
    assert dispatches == [s["name"] for s in plan]


def test_unaccounted_reservation_and_missing_receipt_cannot_restart(run_env):
    directory, plan, dispatches, _ = run_env
    state = read(directory / "state.json")
    state["stage"] = "running"
    persist(directory / "state.json", state)
    with pytest.raises(RuntimeError, match="No verified"):
        bc.run(directory, resume=True)
    assert dispatches == []
