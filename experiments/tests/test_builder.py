import json

import pytest

from experiments import builder_mcp, repair
from experiments.runner import PLANNER_SCHEMA
import jsonschema


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    root = tmp_path / "candidate"
    root.mkdir()
    for name in repair.READ_PATHS:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original source")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "candidate": str(root),
                "read_paths": repair.READ_PATHS,
                "write_paths": repair.WRITE_PATHS,
            }
        )
    )
    monkeypatch.setenv("BUILDER_MANIFEST", str(manifest))
    monkeypatch.setattr(builder_mcp, "calls", 0)
    return root


def test_evaluator_issue_is_valid_but_cannot_dispatch_builder():
    plan = {
        "diagnosis": "Wrong trimmed-face measurement",
        "action": "evaluator_issue",
        "next_instruction": "Supervisory review",
        "preserve": [],
    }
    jsonschema.validate(plan, PLANNER_SCHEMA)
    with pytest.raises(ValueError, match="supervisory"):
        repair.require_plugin_plan(plan)


@pytest.mark.parametrize(
    "path",
    [
        "../experiments/evaluator.py",
        "/etc/passwd",
        ".git/config",
        "plugin/Functions/_utils.cs",
    ],
)
def test_builder_cannot_write_outside_exact_scope(candidate, path):
    with pytest.raises(ValueError, match="scope"):
        builder_mcp.replace_source(path, "hash", "bad")
    assert (candidate / repair.WRITE_PATHS[0]).read_text() == "original source"


def test_builder_requires_fresh_hash_and_rejects_symlink(candidate, tmp_path):
    name = repair.WRITE_PATHS[0]
    original = builder_mcp.read_source(name)
    builder_mcp.replace_source(name, original["sha256"], "updated")
    with pytest.raises(ValueError, match="changed"):
        builder_mcp.replace_source(name, original["sha256"], "stale update")
    protected = tmp_path / "evaluator.py"
    protected.write_text("protected")
    (candidate / name).unlink()
    (candidate / name).symlink_to(protected)
    with pytest.raises(ValueError, match="Symlinks"):
        builder_mcp.replace_source(name, builder_mcp.digest(b"protected"), "attack")
    assert protected.read_text() == "protected"


@pytest.mark.parametrize(
    "attack",
    ["protected", "added", "added_directory", "removed", "mode", "symlink", "none"],
)
def test_controller_rejects_out_of_scope_or_empty_candidate(candidate, attack):
    before = repair.inventory(candidate)
    path = candidate / repair.WRITE_PATHS[0]
    if attack == "protected":
        (candidate / "plugin/Functions/_utils.cs").write_text("changed")
    elif attack == "added":
        (candidate / "new.cs").write_text("new")
    elif attack == "added_directory":
        (candidate / "unexpected").mkdir()
    elif attack == "removed":
        path.unlink()
    elif attack == "mode":
        path.chmod(0o700)
    elif attack == "symlink":
        path.unlink()
        path.symlink_to(candidate / "plugin/Functions/_utils.cs")
    with pytest.raises(ValueError):
        repair.check_candidate(candidate, before)


def test_controller_accepts_only_scoped_content_change(candidate):
    before = repair.inventory(candidate)
    (candidate / repair.WRITE_PATHS[0]).write_text("bounded change")
    assert repair.check_candidate(candidate, before) == [repair.WRITE_PATHS[0]]


@pytest.mark.parametrize(
    "checkpoint",
    [
        {"stage": "building"},
        {"stage": "candidate_ready_for_review", "executed": True},
    ],
)
def test_review_refuses_active_or_executed_candidate(tmp_path, checkpoint):
    (tmp_path / "checkpoint.json").write_text(json.dumps(checkpoint))
    with pytest.raises(ValueError, match="unexecuted"):
        repair.revise(tmp_path, "fix it")


def test_review_uses_fresh_session_and_rechecks_whole_checkout(candidate, monkeypatch):
    import subprocess
    from experiments.runner import save, sha256

    directory = candidate.parent
    for command in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "baseline",
        ],
    ):
        subprocess.run(
            ["git", *command], cwd=candidate, check=True, capture_output=True
        )
    save(directory / "baseline_inventory.json", repair.inventory(candidate))
    (candidate / repair.WRITE_PATHS[0]).write_text("first patch")
    patch = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--binary"], cwd=candidate
    )
    (directory / "candidate.patch").write_bytes(patch)
    save(
        directory / "checkpoint.json",
        {
            "stage": "candidate_ready_for_review",
            "executed": False,
            "patch_sha256": sha256(directory / "candidate.patch"),
        },
    )
    seen = []

    def session(path, prompt, schema, timeout, config):
        seen.append(path.name)
        assert "Controller review" in prompt
        (candidate / repair.WRITE_PATHS[1]).write_text("consistent docs")
        return {"complete": True, "summary": "fixed", "validation_notes": "Not run"}

    monkeypatch.setattr(repair, "run_session", session)
    repair.revise(directory, "Align documentation")
    assert seen[0].startswith("builder-review-")
    result = json.loads((directory / "checkpoint.json").read_text())
    assert result["stage"] == "candidate_ready_for_review"
    assert result["executed"] is False
    assert set(result["changed_paths"]) == set(repair.WRITE_PATHS[:2])
    assert list(directory.glob("builder-review-*-input.patch"))


def test_review_has_exclusive_writer_lock(tmp_path):
    import fcntl

    with (tmp_path / "writer.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            repair.revise(tmp_path, "concurrent write")


def test_gateway_pins_manifest_before_each_access(candidate, monkeypatch):
    from experiments.runner import sha256

    manifest = candidate.parent / "manifest.json"
    monkeypatch.setenv("BUILDER_MANIFEST_SHA256", sha256(manifest))
    builder_mcp.read_source(repair.READ_PATHS[0])
    data = json.loads(manifest.read_text())
    data["write_paths"].append("plugin/Functions/_utils.cs")
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="manifest changed"):
        builder_mcp.read_source(repair.READ_PATHS[0])


def test_scoped_checkpoint_rejects_scope_drift(candidate):
    from experiments.runner import save, sha256

    directory = candidate.parent
    manifest = directory / "manifest.json"
    data = json.loads(manifest.read_text())
    data["scope_version"] = 1
    save(manifest, data)
    pin = {"manifest_sha256": sha256(manifest)}
    save(directory / "scope-lock.json", pin)
    assert repair.repair_scope(directory, pin)["write_paths"] == repair.WRITE_PATHS
    with pytest.raises(ValueError, match="checkpoint"):
        repair.repair_scope(directory, {"manifest_sha256": "different"})
    data["write_paths"].append("plugin/Functions/_utils.cs")
    save(manifest, data)
    with pytest.raises(ValueError, match="changed after dispatch"):
        repair.repair_scope(directory, pin)


def test_per_repair_inventory_gate_has_no_capture_write_fallback(candidate):
    before = repair.inventory(candidate)
    name = "plugin/Functions/_utils.cs"
    (candidate / name).write_text("new scoped source")
    assert repair.check_candidate(candidate, before, [name]) == [name]
    (candidate / repair.WRITE_PATHS[0]).write_text("capture outside new scope")
    with pytest.raises(ValueError, match="protected"):
        repair.check_candidate(candidate, before, [name])


@pytest.mark.parametrize(
    "bad_path",
    [
        "experiments/evaluator.py",
        "plugin/Functions/../Commands/X.cs",
        "/plugin/Functions/X.cs",
        ".git/config",
    ],
)
def test_new_scope_cannot_grant_harness_or_traversal_access(tmp_path, bad_path):
    from experiments.runner import save

    scope = tmp_path / "scope.json"
    evidence = tmp_path / "evidence.json"
    save(scope, {"read_paths": [bad_path], "write_paths": [bad_path]})
    save(evidence, {"planner": {"action": "plugin_issue"}})
    with pytest.raises(ValueError, match="production source paths"):
        repair.scoped_repair(scope, evidence)
