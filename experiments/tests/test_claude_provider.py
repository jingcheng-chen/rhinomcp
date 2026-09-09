import json
from types import SimpleNamespace

import pytest

from experiments import claude_provider as cp, runner
from experiments.workflow.audit import summarize_events


CONFIG = {
    "command": '"python"',
    "args": '["-m", "gateway"]',
    "cwd": '"/tmp"',
    "env": '{ MARKER = "a" }',
    "required": "true",
    "tools.create_object.approval_mode": '"approve"',
}
AGENT = {
    "provider": "claude",
    "model": "explicit-test-model",
    "reasoning_effort": "medium",
}
NAME = "mcp__rhino_experiment__create_object"


def raw(tmp_path, events):
    path = tmp_path / "raw.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events))
    return path


def call(call_id="one", name=NAME):
    return {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": call_id,
                    "name": name,
                    "input": {"object_type": "BOX"},
                }
            ]
        },
    }


def test_explicit_gateway_translation_and_allowlist():
    gateway, allowed = cp.gateway_config(CONFIG)
    assert allowed == [NAME]
    assert gateway["mcpServers"]["rhino_experiment"] == {
        "command": "python",
        "args": ["-m", "gateway"],
        "cwd": "/tmp",
        "env": {"MARKER": "a"},
    }
    with pytest.raises(ValueError, match="allowlist"):
        cp.gateway_config(
            {k: v for k, v in CONFIG.items() if not k.startswith("tools.")}
        )
    with pytest.raises(ValueError):
        cp.gateway_config({**CONFIG, "tools.create_object.approval_mode": '"deny"'})


def test_normalization_preserves_failed_and_unfinished_attempts(tmp_path):
    events = [
        call(),
        call(),
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "one",
                        "is_error": True,
                        "content": "Rejected",
                    }
                ]
            },
        },
        call("two"),
        {"type": "result", "subtype": "error_max_turns", "is_error": True},
    ]
    target = tmp_path / "events.jsonl"
    result = cp.normalize(raw(tmp_path, events), target, [NAME])
    metrics = summarize_events(target)
    assert result["is_error"]
    assert metrics["mcp_attempts"] == 2
    assert metrics["failed_calls"] == 1
    assert metrics["unfinished_calls"] == 1
    assert metrics["usage"] is None


def test_unapproved_tools_and_child_agents_fail_closed(tmp_path):
    for event in [call(name="Bash"), {"parent_tool_use_id": "agent"}]:
        with pytest.raises(RuntimeError):
            cp.normalize(raw(tmp_path, [event]), tmp_path / "events.jsonl", [NAME])


def test_signed_out_preflight_does_not_launch_session(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cp.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout='{"loggedIn":false}', returncode=1),
    )
    monkeypatch.setattr(
        cp.subprocess, "Popen", lambda *a, **k: pytest.fail("Agent launched")
    )
    directory = tmp_path / "session"
    with pytest.raises(RuntimeError, match="signed out"):
        runner.run_session(directory, "task", runner.MODELER_SCHEMA, 5, CONFIG, AGENT)
    assert not directory.exists()


def test_structured_session_uses_restricted_flags_and_retains_raw_events(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        cp.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout='{"loggedIn":true}', returncode=0),
    )
    monkeypatch.setattr(
        cp.subprocess, "check_output", lambda *a, **k: "test-cli-version"
    )
    events = [
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "structured_output": {"summary": "done", "complete": True},
            "usage": {"input_tokens": 2},
        }
    ]

    class Process:
        returncode = 0

        def __init__(self, command, **kwargs):
            assert command[0] == "claude"
            assert command[command.index("--tools") + 1] == ""
            assert "--restricted" in command and "--strict-mcp-config" in command
            assert command[command.index("--permission-mode") + 1] == "dontAsk"
            assert "--dangerously-skip-permissions" not in command
            self.output = kwargs["stdout"]

        def communicate(self, prompt, timeout):
            self.output.write("".join(json.dumps(e) + "\n" for e in events))

    monkeypatch.setattr(cp.subprocess, "Popen", Process)
    directory = tmp_path / "session"
    assert runner.run_session(
        directory, "task", runner.MODELER_SCHEMA, 5, CONFIG, AGENT
    )["complete"]
    assert (directory / "provider-events.jsonl").exists()
    assert json.loads((directory / "status.json").read_text())["status"] == "completed"
    assert summarize_events(directory / "events.jsonl")["usage"] == {"input_tokens": 2}


def test_unknown_provider_is_not_silently_codex(tmp_path):
    with pytest.raises(ValueError):
        runner.run_session(
            tmp_path / "session",
            "task",
            runner.MODELER_SCHEMA,
            5,
            CONFIG,
            {**AGENT, "provider": "unknown"},
        )
