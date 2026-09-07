import asyncio
import copy
import json
from unittest.mock import Mock

import pytest
from experiments.runner import run_session
from experiments.workflow.compare import description_only, summarize
from experiments.workflow.native_mcp import Gateway


def test_suffix_changes_only_description(tmp_path):
    async def check():
        a = [
            t.model_dump()
            for t in await Gateway(1, "a", 2, tmp_path / "log").definitions()
        ]
        b = [
            t.model_dump()
            for t in await Gateway(
                1, "b", 2, tmp_path / "log", description_suffix="\nAnchor guidance"
            ).definitions()
        ]
        description_only(a, b)
        corrupt = copy.deepcopy(b)
        corrupt[0]["inputSchema"]["properties"]["type"]["default"] = "SPHERE"
        with pytest.raises(ValueError, match="only"):
            description_only(a, corrupt)
        with pytest.raises(ValueError, match="No intervention"):
            description_only(a, a)

    asyncio.run(check())


def row(arm, calls, verdict="pass", failed=0):
    return {
        "family": "primitives",
        "arm": arm,
        "task_verdict": verdict,
        "elapsed_seconds": 1,
        "metrics": {"mcp_attempts": calls, "failed_calls": failed},
    }


def test_faster_failure_is_not_improvement():
    result = summarize([row("baseline", 5), row("candidate", 1, "fail")], 2)
    assert result["status"] == "criterion_not_met"
    assert result["promotion_authorized"] is False


def test_incomplete_and_regression_cannot_pass():
    assert summarize([row("baseline", 5)], 2)["status"] == "incomplete"
    assert (
        summarize([row("baseline", 5), row("candidate", 3, failed=1)], 2)["status"]
        == "criterion_not_met"
    )
    assert (
        summarize([row("baseline", 5), row("candidate", 3)], 2)["status"]
        == "criterion_met"
    )


def test_explicit_agent_reaches_cli_without_other_config(tmp_path, monkeypatch):
    def popen(command, **kwargs):
        assert command[command.index("--model") + 1] == "gpt-5.6-terra"
        assert 'model_reasoning_effort="medium"' in command
        assert "--ignore-user-config" in command
        (tmp_path / "session/result.json").write_text("{}")
        return Mock(returncode=0, communicate=Mock())

    monkeypatch.setattr("experiments.runner.subprocess.Popen", popen)
    run_session(
        tmp_path / "session",
        "task",
        {"type": "object"},
        1,
        agent_config={"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
    )
    invocation = json.loads((tmp_path / "session/invocation.json").read_text())
    assert "--model" in invocation["command"]


def test_bad_agent_configuration_rejected_before_launch(tmp_path):
    with pytest.raises(ValueError):
        run_session(
            tmp_path / "session",
            "task",
            {},
            1,
            agent_config={"model": "x", "reasoning_effort": "bogus"},
        )
    assert not (tmp_path / "session").exists()
