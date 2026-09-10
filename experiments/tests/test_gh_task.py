import copy
import json
from pathlib import Path
import pytest
from experiments.gh_task import validate, matches, evaluate
from experiments.runner import load_task
from experiments.workflow.gh_scope import validate_call
from experiments.workflow.validate_gh import variants

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["point_array", "circle_profiles", "loft_sections"])
def test_declared_task(name):
    assert (
        load_task(ROOT / f"experiments/tasks/gh_{name}.json")["type"] == "gh_definition"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_finite_targets(value):
    task = load_task(ROOT / "experiments/tasks/gh_point_array.json")
    task["outputs"][0]["values"][0][0] = value
    with pytest.raises(ValueError):
        validate(task)


def test_values_strict_and_tolerant():
    assert matches([1, {"radius": 2.001}], [1, {"radius": 2}], 0.01)
    assert not matches([True], [1], 0.01)
    assert not matches([1, 2], [1], 0.01)
    assert not matches(float("nan"), 1, 0.01)


@pytest.mark.parametrize(
    "name,args",
    [
        ("gh_add_component", {"component_name": "C# Script"}),
        (
            "gh_add_component",
            {"component_name": "Series", "component_guid": "not-reviewed"},
        ),
        (
            "gh_build_graph",
            {"components": [{"alias": "x", "component_name": "Read File"}]},
        ),
        (
            "gh_mutate_graph",
            {"operations": [{"op": "create", "component_name": "Python 3 Script"}]},
        ),
        ("execute_rhinocommon_csharp_code", {"code": "anything"}),
        ("gh_set_parameter_value", {"value": float("nan")}),
        ("gh_create_document", {"make_active": False}),
    ],
)
def test_host_scope_denials(name, args):
    with pytest.raises(ValueError):
        validate_call(name, args, 0)


def test_host_scope_allows_reviewed_graph_and_caps_size():
    args = {"components": [{"alias": "s", "component_name": "Series"}]}
    validate_call("gh_build_graph", args, 0)
    with pytest.raises(ValueError):
        validate_call("gh_build_graph", args, 32)


def test_missing_artifact_fails_without_agent_claim():
    task = load_task(ROOT / "experiments/tasks/gh_point_array.json")
    report = evaluate(task, {"complete": True})
    assert report["status"] == "fail"


def test_gh_friction_taxonomy():
    from experiments.workflow.flaws import classify

    commands = [
        ("gh_search_components", False, {}),
        ("gh_search_components", False, {}),
        ("gh_run_solution", False, {}),
        ("gh_get_graph", False, {}),
        ("gh_run_solution", False, {}),
        ("gh_connect_components", True, {"error": "missing target input"}),
        ("gh_set_parameter_value", True, {"error": "input parameter not found"}),
        ("gh_layout_components", False, {}),
        ("gh_layout_components", False, {}),
    ]
    rows = [
        {
            "id": str(i),
            "command": c,
            "params": {},
            "failed": f,
            "completed": True,
            "payload": p,
        }
        for i, (c, f, p) in enumerate(commands)
    ]
    subtypes = {f["subtype"] for f in classify(rows) if f["category"] == "gh_friction"}
    assert subtypes == {
        "component_search_churn",
        "repeated_solution_loop",
        "wiring_error",
        "parameter_selector",
        "layout_thrash",
    }


def test_gh_gateway_first_call_identity_scope_and_budget(tmp_path, monkeypatch):
    import asyncio
    from unittest.mock import Mock, AsyncMock
    from experiments.workflow.native_mcp import Gateway
    from experiments.workflow import gh_ownership

    guard = Mock(return_value={"objects": 0})
    monkeypatch.setattr(gh_ownership, "guard", guard)
    production = Mock(call_tool=AsyncMock(return_value={"success": True}))
    gateway = Gateway(
        1,
        "marker",
        5,
        tmp_path / "calls",
        production=production,
        guard=Mock(),
        gh_document="owned",
        tool_names=["gh_create_document", "gh_add_component", "gh_get_graph"],
    )

    async def run():
        with pytest.raises(ValueError, match="start"):
            await gateway.call("gh_add_component", {"component_name": "Series"})
        await gateway.call("gh_create_document", {})
        with pytest.raises(ValueError, match="reviewed"):
            await gateway.call("gh_add_component", {"component_name": "C# Script"})
        guard.side_effect = RuntimeError("identity changed")
        with pytest.raises(RuntimeError, match="identity changed"):
            await gateway.call("gh_add_component", {"component_name": "Series"})
        with pytest.raises(ValueError, match="scope"):
            await gateway.call("run_command", {})
        with pytest.raises(RuntimeError, match="budget"):
            await gateway.call("gh_get_graph", {})

    asyncio.run(run())
    production.call_tool.assert_awaited_once_with("gh_create_document", {})
    assert len((tmp_path / "calls").read_text().splitlines()) == 6


def test_gh_definitions_match_production(tmp_path):
    import asyncio, rhinomcp
    from experiments.workflow.native_mcp import Gateway

    async def run():
        g = Gateway(0, "", 1, tmp_path / "log", gh_document="catalog")
        definitions = await g.definitions()
        original = {t.name: t.model_dump() for t in await rhinomcp.mcp.list_tools()}
        assert len(definitions) == 27
        assert all(
            t.name.startswith("gh_") and t.model_dump() == original[t.name]
            for t in definitions
        )

    asyncio.run(run())


@pytest.mark.parametrize("key", ["point_array", "circle_profiles", "loft_sections"])
def test_live_snapshot_calibration_variants(key):
    task = load_task(ROOT / f"experiments/tasks/gh_{key}.json")
    good = json.loads((ROOT / f"experiments/tests/fixtures/gh/{key}.json").read_text())
    for name, snapshot, expected in variants(good):
        assert (evaluate(task, snapshot)["status"] == "pass") == expected, name


def test_ownership_refuses_swapped_active_doc_and_nonempty_rhino(monkeypatch):
    from experiments.workflow import gh_ownership as gh

    monkeypatch.setattr(gh, "assert_document", lambda *a: {"object_count": 0})
    monkeypatch.setattr(gh, "state", lambda: {"count": 1, "id": "other", "objects": 0})
    with pytest.raises(RuntimeError, match="changed"):
        gh.guard(1, "m", "owned")
    monkeypatch.setattr(gh, "state", lambda: {"count": 1, "id": "owned", "objects": 0})
    monkeypatch.setattr(gh, "assert_document", lambda *a: {"object_count": 1})
    with pytest.raises(RuntimeError, match="changed"):
        gh.guard(1, "m", "owned")


def test_type_inspection_cannot_instantiate_unreviewed_components():
    with pytest.raises(ValueError, match="reviewed"):
        validate_call("gh_get_component_type_info", {"name": "C# Script"}, 0)
