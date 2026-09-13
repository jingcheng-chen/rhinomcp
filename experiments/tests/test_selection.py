import pytest

from experiments import selection as s
from experiments.trial import persist, read
from experiments.runner import sha256


def journal(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    (root / "experiments/runs").mkdir(parents=True)
    monkeypatch.setattr(s, "ROOT", root)
    directory = tmp_path / "selection"
    directory.mkdir()
    entries = {}
    for name, before, after in [
        ("existing.py", b"old", b"new"),
        ("added.py", None, b"added"),
    ]:
        for arm, content in [("before", before), ("after", after)]:
            if content is not None:
                p = directory / arm / name
                p.parent.mkdir(exist_ok=True)
                p.write_bytes(content)
        if before is not None:
            (root / name).write_bytes(before)
        entries[name] = {
            arm: s.file_state(directory / arm / name) for arm in ("before", "after")
        }
    persist(directory / "manifest.json", {"root": str(root), "entries": entries})
    persist(
        directory / "state.json",
        {
            "stage": "prepared",
            "events": [],
            "manifest_sha256": sha256(directory / "manifest.json"),
            "runtime_verified": False,
        },
    )
    return root, directory


def test_source_selection_and_rollback_preserve_old_files(tmp_path, monkeypatch):
    root, directory = journal(tmp_path, monkeypatch)
    s.change_sources(directory)
    assert (root / "existing.py").read_bytes() == b"new"
    assert (root / "added.py").read_bytes() == b"added"
    assert not read(directory / "state.json")["runtime_verified"]
    s.change_sources(directory, rollback=True)
    assert (root / "existing.py").read_bytes() == b"old"
    assert not (root / "added.py").exists()
    s.change_sources(directory)  # Intentional reactivation, never a modeler replay.
    assert (root / "added.py").read_bytes() == b"added"


def test_interrupted_write_can_roll_back_known_partial_state(tmp_path, monkeypatch):
    root, directory = journal(tmp_path, monkeypatch)
    write = s.write_snapshot
    count = 0

    def interrupted(*args):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("simulated interrupted write")
        write(*args)

    monkeypatch.setattr(s, "write_snapshot", interrupted)
    with pytest.raises(OSError):
        s.change_sources(directory)
    assert read(directory / "state.json")["stage"] == "applying"
    assert (root / "existing.py").read_bytes() == b"new"
    monkeypatch.setattr(s, "write_snapshot", write)
    s.change_sources(directory, rollback=True)
    assert (root / "existing.py").read_bytes() == b"old"
    assert not (root / "added.py").exists()


def test_rollback_does_not_overwrite_user_changes(tmp_path, monkeypatch):
    root, directory = journal(tmp_path, monkeypatch)
    s.change_sources(directory)
    (root / "added.py").write_bytes(b"user changed this")
    with pytest.raises(ValueError, match="overwrite changed"):
        s.change_sources(directory, rollback=True)
    assert (root / "existing.py").read_bytes() == b"new"
    assert (root / "added.py").read_bytes() == b"user changed this"


@pytest.mark.parametrize("change", ["snapshot", "manifest", "symlink"])
def test_changed_or_redirected_selection_refused(tmp_path, monkeypatch, change):
    root, directory = journal(tmp_path, monkeypatch)
    if change == "snapshot":
        (directory / "after/added.py").write_bytes(b"changed")
    elif change == "manifest":
        persist(directory / "manifest.json", {})
    else:
        (root / "existing.py").unlink()
        (root / "existing.py").symlink_to(directory / "before/existing.py")
    with pytest.raises(ValueError):
        s.change_sources(directory)
    assert not (root / "added.py").exists()


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a/../outside"])
def test_selection_paths_stay_inside_checkout(tmp_path, name):
    with pytest.raises(ValueError):
        s.target(tmp_path, name)


def evidence(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(s, "ROOT", root)
    monkeypatch.setattr(s.comparison, "check_pins", lambda path: None)
    trial, run = root / "trial", root / "run"
    trial.mkdir()
    run.mkdir()
    (trial / "source").mkdir()
    (trial / "reviewed.patch").write_text("reviewed patch")
    persist(
        trial / "suite.json",
        {"cases": ["old", "new"], "baseline_expectations": {"new": False}},
    )
    baseline = {"mvid": "baseline", "sha256": "old"}
    candidate = {"mvid": "candidate", "sha256": "new"}
    tm = {
        "baseline": baseline,
        "source_inventory": {},
        "suite_inputs": {},
        "patch_sha256": sha256(trial / "reviewed.patch"),
        "suite_sha256": sha256(trial / "suite.json"),
    }
    persist(trial / "manifest.json", tm)
    persist(
        trial / "state.json",
        {
            "stage": "accepted_trial",
            "runtime_dirty": False,
            "candidate_passed": True,
            "candidate": candidate,
            "baseline_cases": {"old": True, "new": False},
            "restored_cases": {"old": True, "new": False},
            "manifest_sha256": sha256(trial / "manifest.json"),
        },
    )
    persist(trial / "comparison.json", {"candidate": {"old": True, "new": True}})
    suite = {
        "tasks": [
            dict(path="discovery", family="patches"),
            dict(path="reserved", family="patches"),
            dict(path="solid", family="solids"),
        ]
    }
    plan = s.comparison.schedule(suite)
    rows = []
    for step in plan:
        status = (
            "fail"
            if step["arm"] == "baseline" and step["entry"]["path"] != "solid"
            else "pass"
        )
        row = {
            "id": step["name"],
            "task": step["entry"]["path"],
            "arm": step["arm"],
            "task_verdict": status,
            "metrics": {"mcp_attempts": 4, "failed_calls": 0},
            "elapsed_seconds": 10,
        }
        rows.append(row)
        child = run / step["name"]
        child.mkdir()
        (child / "candidate.3dm").write_bytes(b"model")
        digest = sha256(child / "candidate.3dm")
        persist(
            child / "artifact.json", {"evaluation_pending": False, "sha256": digest}
        )
        persist(
            child / "evaluation.json",
            {
                "artifact_sha256": digest,
                "status": status,
                "checks": {"geometry": status == "pass"},
                "evaluation_runtime": {"mvid": "baseline"},
            },
        )
    persist(run / "schedule.json", plan)
    persist(
        run / "state.json", {"stage": "complete", "runtime_dirty": False, "rows": rows}
    )
    persist(run / "comparison.json", s.comparison.summarize(rows, plan))
    persist(run / "resources.json", {"pending": None, "stopped": False})
    persist(
        run / "contract.json",
        {
            "evaluation_mode": "trusted_baseline",
            "binaries": {
                "baseline": {"identity": baseline},
                "candidate": {"identity": candidate},
            },
        },
    )
    return trial, run


def test_selection_requires_scoped_benefit_and_reserved_case(tmp_path, monkeypatch):
    trial, run = evidence(tmp_path, monkeypatch)
    result = s.assess(trial, run, ["discovery"], ["reserved"])
    assert result["kind"] == "scoped_workflow_benefit"
    assert result["families_checked"] == ["patches", "solids"]
    with pytest.raises(ValueError, match="reserved"):
        s.assess(trial, run, ["discovery"], [])
    with pytest.raises(ValueError, match="reserved"):
        s.assess(trial, run, ["discovery"], ["discovery"])


@pytest.mark.parametrize(
    "problem",
    [
        "incomplete",
        "dirty",
        "pending_budget",
        "wrong_binary",
        "unrestored",
        "candidate_failure",
        "changed_model",
        "changed_verdict",
    ],
)
def test_incomplete_or_inconsistent_evidence_cannot_select(
    tmp_path, monkeypatch, problem
):
    trial, run = evidence(tmp_path, monkeypatch)
    if problem in ("incomplete", "dirty", "candidate_failure"):
        value = read(run / "state.json")
        if problem == "incomplete":
            value["stage"] = "running"
        elif problem == "dirty":
            value["runtime_dirty"] = True
        else:
            value["rows"][1]["task_verdict"] = "fail"
            persist(
                run / "comparison.json",
                s.comparison.summarize(value["rows"], read(run / "schedule.json")),
            )
        persist(run / "state.json", value)
    elif problem == "pending_budget":
        persist(
            run / "resources.json",
            {"pending": {"name": "unfinished"}, "stopped": False},
        )
    elif problem == "wrong_binary":
        value = read(run / "contract.json")
        value["binaries"]["candidate"]["identity"]["mvid"] = "unrelated"
        persist(run / "contract.json", value)
    elif problem == "unrestored":
        value = read(trial / "state.json")
        value["restored_cases"]["old"] = False
        persist(trial / "state.json", value)
    elif problem == "changed_model":
        (run / "task-1-pair-1-candidate/candidate.3dm").write_bytes(b"replaced")
    else:
        path = run / "task-1-pair-1-candidate/evaluation.json"
        value = read(path)
        value["checks"]["geometry"] = False
        persist(path, value)
    with pytest.raises(ValueError):
        s.assess(trial, run, ["discovery"], ["reserved"])


def test_export_permissions_and_byte_patch_preserve_working_tree_modes(
    tmp_path, monkeypatch
):
    root = tmp_path / "checkout"
    (root / "experiments/runs").mkdir(parents=True)
    (root / "contracts").mkdir()
    old = root / "contracts/protocol.json"
    old.write_bytes(b"old")
    old.chmod(0o600)
    monkeypatch.setattr(s, "ROOT", root)
    trial, run, builder = (
        tmp_path / name for name in ("trial", "comparison", "builder")
    )
    for directory in (trial, run, builder):
        directory.mkdir()
    new_name = "server/src/rhinomcp/tools/added.py"
    scope = {"write_paths": ["contracts/protocol.json"], "create_paths": [new_name]}
    monkeypatch.setattr(s, "assess", lambda *a: {"reviewed": True})
    monkeypatch.setattr(
        s.capability, "reviewed_source", lambda *a: (scope, b"byte patch")
    )
    (trial / "reviewed.patch").write_bytes(b"byte patch")
    for name in scope["write_paths"] + scope["create_paths"]:
        path = trial / "source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"new")
        path.chmod(0o664)
    baseline = {"mvid": "old", "sha256": "old"}
    candidate = {"mvid": "new", "sha256": "new"}
    persist(trial / "manifest.json", {"repair": str(builder), "baseline": baseline})
    persist(trial / "state.json", {"candidate": candidate})
    persist(builder / "checkpoint.json", {})
    persist(
        builder / "baseline_inventory.json",
        {"contracts/protocol.json": {**s.file_state(old), "mode": 0o664}},
    )
    persist(
        run / "contract.json",
        {
            "binaries": {
                "baseline": {"identity": baseline},
                "candidate": {"identity": candidate},
            }
        },
    )
    (run / "baseline.rhp").write_bytes(b"old binary")
    (run / "candidate.rhp").write_bytes(b"new binary")
    directory = s.prepare(trial, run, "review", ["discovery"], ["reserved"])
    s.change_sources(directory)
    assert s.file_state(old)["mode"] == 0o600
    assert s.file_state(root / new_name)["mode"] == 0o644
    s.change_sources(directory, rollback=True)
    assert old.read_bytes() == b"old"
    assert s.file_state(old)["mode"] == 0o600
    assert not (root / new_name).exists()


@pytest.fixture
def released_checkout(tmp_path, monkeypatch):
    import importlib
    import subprocess
    from experiments import rhino_trial

    root = tmp_path / "release"
    (root / "experiments/runs").mkdir(parents=True)
    (root / "plugin").mkdir()
    source = root / "plugin/source.cs"
    source.write_text("release source")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)

    git("init", "-q")
    git("add", "plugin/source.cs")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "release",
    )
    git("tag", "releases/0.4.0")
    binary = tmp_path / "release.rhp"
    binary.write_bytes(b"release binary")
    identity = {"mvid": "release-mvid", "sha256": sha256(binary)}
    observed = {
        "version": "0.4.0.0",
        "docs": [{"modified": False}],
        "path": None,
        "object_count": 0,
        "marker": None,
        "mvid": identity["mvid"],
        "assembly": str(binary),
    }
    monkeypatch.setattr(s, "ROOT", root)
    monkeypatch.setattr(rhino_trial, "runtime", lambda: observed)
    module = importlib.import_module("rhinomcp.tools.describe_capabilities")
    monkeypatch.setattr(
        module,
        "describe_capabilities",
        lambda ctx: {"version": "0.4.0", "server_version": "0.4.0"},
    )
    return root, source, identity, observed


def test_release_selection_records_verified_sources_without_rewriting(
    released_checkout,
):
    root, source, identity, _ = released_checkout
    directory = s.select_release("releases/0.4.0", identity, "0.4.0")
    manifest, state = s.load(directory)
    assert manifest["kind"] == "released_baseline"
    assert manifest["candidate"] == identity
    assert state["stage"] == "selected" and state["runtime_verified"]
    assert source.read_text() == "release source"
    # The ordinary journal integrity gate also protects release snapshots.
    (directory / "after/plugin/source.cs").write_text("tampered")
    with pytest.raises(ValueError, match="snapshot changed"):
        s.load(directory)


@pytest.mark.parametrize(
    "problem",
    ["source", "untracked", "modified", "version", "binary", "objects", "marker"],
)
def test_release_selection_rejects_unverified_state(released_checkout, problem):
    root, source, identity, observed = released_checkout
    if problem == "source":
        source.write_text("local edit")
    elif problem == "untracked":
        (root / "plugin/extra.cs").write_text("unreleased")
    elif problem == "modified":
        observed["docs"][0]["modified"] = True
    elif problem == "version":
        observed["version"] = "0.3.2.0"
    elif problem == "binary":
        identity = {**identity, "sha256": "different"}
    elif problem == "objects":
        observed["object_count"] = 1
    else:
        observed["marker"] = "another-run"
    with pytest.raises(ValueError):
        s.select_release("releases/0.4.0", identity, "0.4.0")
