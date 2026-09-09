"""Exercise real adapter subprocesses against a disposable file-based runtime.

This is controller verification, not Rhino geometry or live installation evidence.
"""

import hashlib
from pathlib import Path
import subprocess

import pytest

from experiments import repair
from experiments.runner import save
from experiments.trial import Trial, locked, prepare, read

ADAPTER = """import hashlib, json, pathlib, shutil, sys, time
request = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(__file__).parent
mode = (root / "mode").read_text()
if mode == "venv": import rhinomcp
active = root / "active.rhp"
trial = pathlib.Path(request["trial"])
action = request["action"]
with (root / "calls").open("a") as log:
    log.write(action + "\\n")
def identity(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mvid": "baseline" if path.read_bytes() == b"baseline" else "candidate"}
if action == "build":
    if mode == "build_fail": sys.exit(2)
    target = pathlib.Path(request["candidate_binary"])
    target.write_bytes(b"candidate")
    result = identity(target)
elif action == "probe":
    result = identity(active)
    if mode == "wrong_identity" and active.read_bytes() != b"baseline":
        result["mvid"] = "wrong"
elif action in ("install", "restore"):
    key = "candidate_binary" if action == "install" else "baseline_binary"
    if action == "restore" and mode == "restore_fail": sys.exit(3)
    shutil.copyfile(request[key], active)
    if action == "install" and mode == "partial_install": sys.exit(4)
    if action == "install" and mode == "source_drift":
        (pathlib.Path(request["source"]) / "plugin/Functions/CaptureViewport.cs").write_text("drift")
    result = {"ok": True}
else:
    candidate = active.read_bytes() != b"baseline"
    if candidate and mode == "timeout": time.sleep(10)
    cases = {name: True for name in json.loads(pathlib.Path(request["suite"]).read_text())["cases"]}
    if candidate and mode in ("regression", "restore_fail"): cases["capture"] = False
    if not candidate and mode == "baseline_fail": cases["capture"] = False
    if candidate and mode == "missing_case": del cases["capture"]
    if candidate and mode == "string_verdict": cases["capture"] = "true"
    result = {"identity": identity(active), "cases": cases}
    if candidate and mode == "wrong_evidence": result["identity"]["mvid"] = "baseline"
pathlib.Path(sys.argv[2]).write_text(json.dumps(result))
"""


@pytest.fixture
def prepared(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    for name in repair.READ_PATHS:
        path = candidate / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("baseline source")
    for args in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "baseline",
        ],
    ):
        subprocess.run(
            ["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false", *args],
            cwd=candidate,
            check=True,
            capture_output=True,
        )
    save(tmp_path / "baseline_inventory.json", repair.inventory(candidate))
    (candidate / repair.WRITE_PATHS[0]).write_text("reviewed patch")
    repair.finish_candidate(tmp_path, {"complete": True})
    (tmp_path / "baseline.rhp").write_bytes(b"baseline")
    (tmp_path / "active.rhp").write_bytes(b"baseline")
    adapter = tmp_path / "adapter.py"
    adapter.write_text(ADAPTER)
    (tmp_path / "mode").write_text("pass")
    (tmp_path / "judge.py").write_text("# Fixed evaluator fixture")
    save(
        tmp_path / "suite.json",
        {"cases": ["capture", "geometry"], "inputs": ["judge.py"]},
    )
    directory = prepare(
        tmp_path,
        tmp_path / "baseline.rhp",
        "baseline",
        tmp_path / "suite.json",
        adapter,
        tmp_path / "runtime.lock",
        "Reviewed exact patch; test runtime only.",
    )
    return tmp_path, directory


def run_mode(prepared, mode, timeout=3):
    root, directory = prepared
    (root / "mode").write_text(mode)
    state = Trial(directory, timeout).run()
    return root, directory, state


def test_pass_restores_baseline_and_never_promotes(prepared):
    root, directory, state = run_mode(prepared, "pass")
    assert state["stage"] == "accepted_trial"
    assert state["promoted"] is False
    assert state["runtime_dirty"] is False
    assert (root / "active.rhp").read_bytes() == b"baseline"
    assert read(directory / "comparison.json")["regressions"] == []
    calls = (root / "calls").read_text()
    assert Trial(directory).run() == state
    assert (root / "calls").read_text() == calls  # terminal resume is idempotent
    assert read(root / "checkpoint.json")["stage"] == "validation_registered"
    with pytest.raises(ValueError, match="unexecuted"):
        repair.revise(root, "Must not revise a registered trial")


@pytest.mark.parametrize(
    "mode",
    [
        "regression",
        "wrong_identity",
        "wrong_evidence",
        "missing_case",
        "string_verdict",
        "partial_install",
        "source_drift",
        "timeout",
    ],
)
def test_failures_after_install_restore_verified_baseline(prepared, mode):
    root, directory, state = run_mode(
        prepared, mode, timeout=0.3 if mode == "timeout" else 3
    )
    assert state["stage"] == "rejected", state
    assert state["runtime_dirty"] is False
    assert state["restored_cases"] == {"capture": True, "geometry": True}
    assert (root / "active.rhp").read_bytes() == b"baseline"
    if mode == "regression":
        assert read(directory / "comparison.json")["regressions"] == ["capture"]


@pytest.mark.parametrize("mode", ["build_fail", "baseline_fail"])
def test_failure_before_install_never_mutates_runtime(prepared, mode):
    root, _, state = run_mode(prepared, mode)
    assert state["stage"] == "rejected"
    calls = (root / "calls").read_text().splitlines()
    assert "install" not in calls
    assert "restore" not in calls
    assert (root / "active.rhp").read_bytes() == b"baseline"


def test_restore_failure_remains_unresolved_and_can_retry(prepared):
    root, directory, state = run_mode(prepared, "restore_fail")
    assert state["stage"] == "recovery_required"
    assert state["runtime_dirty"] is True
    assert (root / "active.rhp").read_bytes() == b"candidate"
    (root / "mode").write_text("pass")
    trial = Trial(directory)
    # An unresolved command is treated conservatively after a process restart.
    assert trial.run()["stage"] == "operator_required"
    trial.acknowledge_child_stopped()
    state = trial.run()
    assert state["stage"] == "rejected"
    assert (root / "active.rhp").read_bytes() == b"baseline"
    assert (root / "calls").read_text().splitlines().count("install") == 1


def test_interrupted_install_requires_quiescence_then_recovers_without_replay(prepared):
    root, directory = prepared
    (root / "active.rhp").write_bytes(b"candidate")
    state = read(directory / "state.json")
    state.update(
        stage="install",
        runtime_dirty=True,
        pending="unresolved-install",
        child_group=12345,
    )
    save(directory / "state.json", state)
    trial = Trial(directory)
    assert trial.run()["stage"] == "operator_required"
    assert not (root / "calls").exists()
    trial.acknowledge_child_stopped()
    assert trial.run()["stage"] == "rejected"
    assert "install" not in (root / "calls").read_text().splitlines()
    assert (root / "active.rhp").read_bytes() == b"baseline"


@pytest.mark.parametrize(
    "name", ["adapter.py", "baseline.rhp", "suite.json", "review.txt"]
)
def test_pinned_inputs_fail_closed(prepared, name):
    root, directory = prepared
    path = root / name if name == "adapter.py" else directory / name
    path.write_text("changed after review")
    state = Trial(directory).run()
    assert state["stage"] in ("rejected", "recovery_required")
    assert (root / "active.rhp").read_bytes() == b"baseline"
    assert (
        not (root / "calls").exists() or "install" not in (root / "calls").read_text()
    )


def test_runtime_lock_prevents_overlapping_trials(prepared):
    root, directory = prepared
    with locked(root / "runtime.lock"):
        with pytest.raises(BlockingIOError):
            Trial(directory).run()
    assert not (root / "calls").exists()


def test_stale_source_is_rejected_before_build(prepared):
    root, directory = prepared
    (directory / "source" / repair.WRITE_PATHS[0]).write_text("unreviewed")
    assert Trial(directory).run()["stage"] == "rejected"
    assert (root / "calls").read_text().splitlines() == ["probe"]


def test_manifest_edit_does_not_authorize_a_new_adapter(prepared):
    root, directory = prepared
    manifest = read(directory / "manifest.json")
    manifest["adapter_sha256"] = hashlib.sha256(b"changed").hexdigest()
    save(directory / "manifest.json", manifest)
    assert Trial(directory).run()["stage"] == "recovery_required"
    assert not (root / "calls").exists()


def test_evaluator_change_cannot_be_used_for_candidate_acceptance(prepared):
    root, directory = prepared
    (root / "judge.py").write_text("# Changed judge")
    assert Trial(directory).run()["stage"] == "recovery_required"
    assert not (root / "calls").exists()


def test_prepare_rejects_reuse_of_registered_candidate(prepared):
    root, _ = prepared
    with pytest.raises(ValueError, match="unexecuted"):
        prepare(
            root,
            root / "baseline.rhp",
            "baseline",
            root / "suite.json",
            root / "adapter.py",
            root / "runtime.lock",
            "Second review",
        )


def test_adapter_retains_virtual_environment_dependencies(prepared):
    _, _, state = run_mode(prepared, "venv")
    assert state["stage"] == "accepted_trial"


def test_baseline_expectations_are_explicit_and_boolean():
    from experiments.trial import baseline_expectations

    assert baseline_expectations(
        {"cases": ["old", "new"], "baseline_expectations": {"new": False}}
    ) == {"old": True, "new": False}
    for expected in ({"unknown": False}, {"new": "false"}, []):
        with pytest.raises(ValueError, match="baseline expectations"):
            baseline_expectations(
                {"cases": ["old", "new"], "baseline_expectations": expected}
            )


@pytest.mark.parametrize("improves", [True, False])
def test_new_capability_improves_without_redefining_baseline(prepared, improves):
    root, directory = prepared
    manifest = read(directory / "manifest.json")
    suite = read(directory / "suite.json")
    suite["baseline_expectations"] = {"capture": False}
    save(directory / "suite.json", suite)
    from experiments.runner import sha256

    manifest["suite_sha256"] = sha256(directory / "suite.json")
    save(directory / "manifest.json", manifest)
    adapter = Path(manifest["adapter"])
    adapter.write_text(
        adapter.read_text().replace(
            'if not candidate and mode == "baseline_fail":',
            'if not candidate or mode == "no_improvement":',
        )
    )
    if not improves:
        (root / "mode").write_text("no_improvement")
    manifest["adapter_sha256"] = sha256(adapter)
    save(directory / "manifest.json", manifest)
    state = read(directory / "state.json")
    state["manifest_sha256"] = sha256(directory / "manifest.json")
    save(directory / "state.json", state)
    result = Trial(directory).run()
    assert result["stage"] == ("accepted_trial" if improves else "rejected")
    assert result["baseline_cases"]["capture"] is False
    assert result["restored_cases"]["capture"] is False
    comparison = read(directory / "comparison.json")
    assert comparison["improvements"] == (["capture"] if improves else [])
    assert comparison["unmet_requirements"] == ([] if improves else ["capture"])
    assert comparison["regressions"] == []
