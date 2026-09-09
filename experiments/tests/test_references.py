import json

import pytest

from experiments import references, runner


def test_reference_task_has_no_dimensions_in_public_brief():
    task = runner.load_task(runner.ROOT / "experiments/tasks/reference_box.json")
    assert task["dimensions"] == [70, 40, 30]
    assert "70" not in task["instruction"]
    assert "40" not in task["instruction"]
    assert "30" not in task["instruction"]


@pytest.mark.parametrize("dimensions", [[75, 40, 30], [90, 40, 30]])
def test_reference_task_rejects_unreadable_or_off_canvas_dimensions(
    tmp_path, dimensions
):
    task = json.loads(
        (runner.ROOT / "experiments/tasks/reference_box.json").read_text()
    )
    task["dimensions"] = dimensions
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task))
    with pytest.raises(runner.jsonschema.ValidationError):
        runner.load_task(path)


def test_reference_feedback_cannot_leak_planner_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "identity", lambda: pytest.fail("Rhino reached"))
    with pytest.raises(ValueError, match="hidden answers"):
        runner.run_locked(
            runner.ROOT / "experiments/tasks/reference_box.json",
            10,
            tmp_path,
            tmp_path / "feedback.json",
        )


def test_reference_gateway_rejects_paths_and_changed_images(tmp_path, monkeypatch):
    monkeypatch.setenv("EXPERIMENT_REFERENCE_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="Unknown"):
        references.reference_image("../reference.3dm")
    (tmp_path / "top.png").write_bytes(b"original")
    (tmp_path / "views.json").write_text(
        json.dumps({"views": {"top": {"sha256": runner.sha256(tmp_path / "top.png")}}})
    )
    assert references.reference_image("top").data == b"original"
    (tmp_path / "top.png").write_bytes(b"replacement")
    with pytest.raises(RuntimeError, match="changed"):
        references.reference_image("top")


@pytest.mark.parametrize("image_task", [True, False])
def test_runner_exposes_only_public_brief_and_task_specific_image_tool(
    tmp_path, monkeypatch, image_task
):
    assembly = tmp_path / "plugin.rhp"
    assembly.write_bytes(b"plugin")
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
    monkeypatch.setattr(runner, "measure", lambda path: {})
    monkeypatch.setattr(runner, "evaluate", lambda task, measured: {"status": "pass"})
    monkeypatch.setattr(runner, "capture", lambda *args: None)

    def save_candidate(path, *args):
        path.write_bytes(b"candidate")
        return runner.sha256(path)

    monkeypatch.setattr(runner, "save_candidate", save_candidate)

    def generate(task, directory):
        directory.mkdir()
        (directory / "reference.3dm").write_bytes(b"secret")
        return {
            "model_sha256": runner.sha256(directory / "reference.3dm"),
            "public": {"views": {}},
        }

    monkeypatch.setattr(references, "generate", generate)
    calls = []

    def session(directory, prompt, schema, timeout, config=None):
        calls.append((prompt, config))
        return (
            {"complete": True, "summary": "modeled"} if config else {"action": "accept"}
        )

    monkeypatch.setattr(runner, "run_session", session)
    name = "reference_box.json" if image_task else "box.json"
    runner.run_locked(runner.ROOT / "experiments/tasks" / name, 10, tmp_path)
    prompt, config = calls[0]
    assert '"dimensions":' not in prompt
    assert "reference.3dm" not in prompt
    assert ("get_reference_image" in json.loads(config["disabled_tools"])) != image_task
    if image_task:
        assert "70" not in prompt
        assert config["tools.get_reference_image.approval_mode"] == '"approve"'
        assert "EXPERIMENT_REFERENCE_DIR" in config["env"]
        # Gold fields are only in the planner's later, isolated prompt.
        assert '"dimensions": [70, 40, 30]' in calls[1][0]
