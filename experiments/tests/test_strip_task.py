import json
import copy

import pytest

from experiments import runner, modeler_mcp, strip_task
from experiments.tests.test_strip import correct


def task():
    return runner.load_task(runner.ROOT / "experiments/tasks/quarter_strip_origin.json")


def test_strip_task_uses_strict_shape_and_finite_pose(tmp_path):
    original = task()
    for changes in (
        {"dimensions": [111, 110, 10]},
        {"rotation_z_degrees": 90},
        {"translation": [float("nan"), 0, 0]},
    ):
        path = tmp_path / "task.json"
        path.write_text(json.dumps({**original, **changes}))
        with pytest.raises((ValueError, runner.jsonschema.ValidationError)):
            runner.load_task(path)


def test_task_judge_rejects_wrong_shape_units_and_extra_objects():
    assert strip_task.evaluate(task(), correct())["status"] == "pass"
    for change in (
        {"volume": None},
        {"area": 0},
        {"min": [150, -80, 25]},
        {"naked_edges": 8},
    ):
        measured = correct()
        measured["objects"][0].update(change)
        assert strip_task.evaluate(task(), measured)["status"] == "fail"
    measured = correct()
    measured["objects"].append(copy.deepcopy(measured["objects"][0]))
    assert strip_task.evaluate(task(), measured)["status"] == "fail"


def test_measurement_applies_inverse_pose_only_to_duplicate(tmp_path):
    posed = {**task(), "translation": [150, -80, 25]}
    code = strip_task.measurement_code(tmp_path / "model.3dm", posed)
    assert (
        "brep=brep.DuplicateBrep();\n  brep.Transform(Transform.Translation(-150, 80, -25));"
        in code
    )
    assert ".Write(" not in code


def test_sweep_gateway_checks_document_and_surfaces_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(modeler_mcp, "guard", lambda: calls.append("guard"))

    def sweep(*args, **kwargs):
        assert calls == ["guard"]
        assert kwargs["cap_planar_ends"] is True
        return {"success": False, "message": "capping failed"}

    monkeypatch.setattr(modeler_mcp, "original_sweep", sweep)
    with pytest.raises(RuntimeError, match="capping failed"):
        modeler_mcp.sweep1("rail", ["profile"], True)


@pytest.mark.parametrize(
    "name,enabled", [("box", False), ("quarter_strip_origin", True)]
)
def test_sweep_is_enabled_only_for_strip_task(tmp_path, monkeypatch, name, enabled):
    assembly = tmp_path / "plugin.rhp"
    assembly.write_bytes(b"baseline")
    monkeypatch.setattr(
        runner,
        "identity",
        lambda: {
            "object_count": 0,
            "path": None,
            "document": 1,
            "assembly": str(assembly),
        },
    )
    monkeypatch.setattr(runner, "script", lambda code: "")
    monkeypatch.setattr(runner, "measure", lambda *args: {})
    monkeypatch.setattr(runner, "evaluate", lambda *args: {"status": "pass"})
    monkeypatch.setattr(runner, "capture", lambda *args: None)

    def save_candidate(path, *args):
        path.write_bytes(b"model")
        return runner.sha256(path)

    monkeypatch.setattr(runner, "save_candidate", save_candidate)
    configs = []

    def session(directory, prompt, schema, timeout, config=None):
        if config:
            configs.append(config)
            return {"complete": True, "summary": "done"}
        return {"action": "accept"}

    monkeypatch.setattr(runner, "run_session", session)
    runner.run_locked(runner.ROOT / f"experiments/tasks/{name}.json", 5, tmp_path)
    assert ("sweep1" not in json.loads(configs[0]["disabled_tools"])) is enabled
    assert ("tools.sweep1.approval_mode" in configs[0]) is enabled


def test_new_baseline_requires_all_previous_capabilities_and_both_agent_tasks():
    from experiments.trial import baseline_expectations

    root = runner.ROOT / "experiments/harness"
    old = json.loads((root / "trial-sweep-cap.json").read_text())
    new = json.loads((root / "trial-preservation-v2.json").read_text())
    assert new["cases"] == old["cases"] + [
        "model/quarter_strip_origin",
        "model/quarter_strip_translated",
    ]
    assert len(new["cases"]) == 52
    assert all(baseline_expectations(new).values())
