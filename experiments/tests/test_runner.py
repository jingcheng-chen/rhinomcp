import json
import subprocess
import sys

import pytest

from experiments import modeler_mcp, runner


@pytest.mark.parametrize("value", ["0; throw new Exception()", -1, float("nan")])
def test_task_rejects_invalid_tolerance_before_rhino_access(tmp_path, value):
    task = json.loads((runner.ROOT / "experiments/tasks/box.json").read_text())
    task["linear_tolerance"] = value
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task))
    with pytest.raises((ValueError, runner.jsonschema.ValidationError)):
        runner.load_task(path)


def test_load_canonical_task():
    assert runner.load_task(runner.ROOT / "experiments/tasks/box.json")[
        "dimensions"
    ] == [100, 50, 30]


def test_gateway_refuses_changed_document(monkeypatch):
    monkeypatch.setenv("EXPERIMENT_DOCUMENT", "1")
    monkeypatch.setenv("EXPERIMENT_MARKER", "test")
    monkeypatch.setenv("EXPERIMENT_MAX_CALLS", "12")
    monkeypatch.setattr(modeler_mcp, "calls", 0)

    def refuse(*args):
        raise RuntimeError("Active document changed")

    monkeypatch.setattr(modeler_mcp, "assert_document", refuse)
    monkeypatch.setattr(
        modeler_mcp, "original_create", lambda *a, **k: pytest.fail("Mutation reached")
    )
    with pytest.raises(RuntimeError, match="document changed"):
        modeler_mcp.create_object("BOX", {})


def test_gateway_call_budget(monkeypatch):
    monkeypatch.setenv("EXPERIMENT_MAX_CALLS", "12")
    monkeypatch.setattr(modeler_mcp, "calls", 12)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        modeler_mcp.guard()


@pytest.mark.parametrize("mode", ["valid", "invalid_schema", "timeout", "crash"])
def test_session_completion_and_failure_records(tmp_path, monkeypatch, mode):
    real_popen = subprocess.Popen
    child = None

    def fake_client(command, **kwargs):
        nonlocal child
        output = command[command.index("--output-last-message") + 1]
        code = "import sys, pathlib, time; sys.stdin.read(); "
        if mode == "timeout":
            code += "time.sleep(30)"
        elif mode == "crash":
            code += "sys.exit(7)"
        else:
            payload = (
                {"summary": "done", "complete": True}
                if mode == "valid"
                else {"complete": "yes"}
            )
            code += f"pathlib.Path({output!r}).write_text({json.dumps(payload)!r})"
        child = real_popen([sys.executable, "-c", code], **kwargs)
        return child

    monkeypatch.setattr(runner.subprocess, "Popen", fake_client)
    directory = tmp_path / mode
    if mode == "valid":
        assert runner.run_session(directory, "task", runner.MODELER_SCHEMA, 5)[
            "complete"
        ]
    else:
        with pytest.raises(Exception):
            runner.run_session(
                directory,
                "task",
                runner.MODELER_SCHEMA,
                0.2 if mode == "timeout" else 5,
            )
    status = json.loads((directory / "status.json").read_text())["status"]
    assert status == {"valid": "completed", "timeout": "timed_out"}.get(mode, "failed")
    assert child.poll() is not None
