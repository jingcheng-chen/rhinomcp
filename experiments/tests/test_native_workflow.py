import asyncio
import json
from unittest.mock import AsyncMock, Mock

import pytest
import rhinomcp
from experiments.workflow.native_mcp import Gateway, TOOLS
from experiments.workflow.pilot import load_suite
from experiments.runner import ROOT


def test_native_definitions_are_identical_and_execution_is_excluded(tmp_path):
    async def check():
        original = {t.name: t.model_dump() for t in await rhinomcp.mcp.list_tools()}
        gateway = Gateway(1, "run", 3, tmp_path / "calls")
        actual = await gateway.definitions()
        assert {t.name: t.model_dump() for t in actual} == {
            n: original[n] for n in TOOLS
        }
        assert "execute_rhinocommon_csharp_code" not in TOOLS
        assert "run_command" not in TOOLS
        assert "describe_command" not in TOOLS

    asyncio.run(check())


def test_guard_budget_and_scope_block_before_production(tmp_path):
    async def check():
        production = Mock(call_tool=AsyncMock(return_value={"result": "unchanged"}))
        guard = Mock()
        gateway = Gateway(12, "owner", 2, tmp_path / "calls", production, guard)
        assert await gateway.call("create_object", {"type": "BOX"}) == {
            "result": "unchanged"
        }
        with pytest.raises(ValueError, match="scope"):
            await gateway.call("run_command", {})
        with pytest.raises(RuntimeError, match="budget"):
            await gateway.call("create_object", {})
        production.call_tool.assert_awaited_once_with("create_object", {"type": "BOX"})
        guard.assert_called_once_with(12, "owner")
        assert [
            json.loads(x)["status"]
            for x in (tmp_path / "calls").read_text().splitlines()
        ] == ["returned", "error", "error"]

    asyncio.run(check())


def test_document_change_blocks_mutation(tmp_path):
    async def check():
        production = Mock(call_tool=AsyncMock())
        gateway = Gateway(
            12,
            "owner",
            2,
            tmp_path / "calls",
            production,
            Mock(side_effect=RuntimeError("changed")),
        )
        with pytest.raises(RuntimeError, match="changed"):
            await gateway.call("create_object", {})
        production.call_tool.assert_not_called()

    asyncio.run(check())


def test_pilot_reuses_two_existing_task_families():
    suite = load_suite(ROOT / "experiments/workflow/pilot.json")
    assert len({e["family"] for e in suite["tasks"]}) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"call_budget": 0},
        {"timeout_seconds": True},
        {"tasks": [{"family": "escape", "path": "experiments/../server/main.py"}]},
        {"unexpected": "field"},
    ],
)
def test_invalid_suite_rejected_before_rhino(tmp_path, change):
    suite = json.loads((ROOT / "experiments/workflow/pilot.json").read_text())
    suite.update(change)
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(suite))
    with pytest.raises(ValueError):
        load_suite(path)


def test_reviewed_extension_cannot_add_scripting_or_remove_native_tools(tmp_path):
    from experiments.workflow.native_mcp import Gateway, TOOLS
    import pytest

    for names in [
        TOOLS[:-1],
        (*TOOLS, "run_command"),
        (*TOOLS, "execute_rhinocommon_csharp_code"),
        (*TOOLS, "execute_rhinoscript_python_code"),
        (*TOOLS, TOOLS[0]),
    ]:
        with pytest.raises(ValueError, match="reviewed tool extension"):
            Gateway(0, "", 1, tmp_path / "log", tool_names=names)


def test_full_catalog_preserves_all_definitions_and_scripts(tmp_path):
    async def check():
        gateway = Gateway(1, "run", 10, tmp_path / "log", full_catalog=True)
        definitions = await gateway.definitions()
        production = await rhinomcp.mcp.list_tools()
        assert {t.name: t.model_dump() for t in definitions} == {
            t.name: t.model_dump() for t in production
        }
        assert {"run_command", "execute_rhinocommon_csharp_code"} <= set(
            gateway.tool_names
        )

    asyncio.run(check())


def test_full_catalog_still_enforces_rhino_ownership_and_excludes_unowned_gh(tmp_path):
    async def check():
        production = Mock(call_tool=AsyncMock(return_value={"success": True}))
        guard = Mock()
        gateway = Gateway(
            1,
            "run",
            10,
            tmp_path / "log",
            production,
            guard,
            tool_names=("create_object", "gh_clear_canvas"),
            full_catalog=True,
        )
        await gateway.call("create_object", {"type": "BOX"})
        assert guard.call_count == 2
        with pytest.raises(ValueError, match="Grasshopper"):
            await gateway.call("gh_clear_canvas", {})
        production.call_tool.assert_awaited_once()

    asyncio.run(check())


@pytest.mark.parametrize(
    "name",
    [
        "run_command",
        "execute_rhinocommon_csharp_code",
        "execute_rhinoscript_python_code",
    ],
)
def test_host_execution_attempts_are_refused_recorded_and_consume_budget(
    tmp_path, name
):
    async def check():
        production = Mock(call_tool=AsyncMock())
        guard = Mock()
        log = tmp_path / "calls"
        gateway = Gateway(
            1,
            "run",
            1,
            log,
            production,
            guard,
            tool_names=(name, "create_object"),
            full_catalog=True,
        )
        arguments = {"code": "agent-authored"}
        with pytest.raises(ValueError, match="Execution tools are refused"):
            await gateway.call(name, arguments)
        with pytest.raises(RuntimeError, match="budget"):
            await gateway.call("create_object", {})
        production.call_tool.assert_not_awaited()
        guard.assert_not_called()
        events = [json.loads(line) for line in log.read_text().splitlines()]
        assert events[0]["tool"] == name
        assert events[0]["arguments"] == arguments
        assert events[0]["status"] == "error"
        assert "M5" in events[0]["error"]
        assert events[1]["attempt"] == 2

    asyncio.run(check())
