"""Supervised, evidence-gated capability selection with reversible source writes.

This is a local integrity/rollback mechanism, not an adversarial security sandbox.
Runtime installation remains the independently verified desktop lifecycle.
"""

import argparse
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import time
import uuid

from experiments import capability
from experiments.repair import inventory
from experiments.runner import ROOT, sha256
from experiments.trial import locked, persist, read
from experiments.workflow import binary_compare as comparison


def target(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or str(relative) != name:
        raise ValueError("Unsafe selection path")
    path = root / name
    if any(part.is_symlink() for part in [path, *path.parents] if part != root.parent):
        raise ValueError("Selection cannot traverse symlinks")
    path.resolve().relative_to(root.resolve())
    return path


def file_state(path):
    if path.is_symlink():
        raise ValueError("Selection cannot replace symlinks")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError("Selection target is not an ordinary file")
    return {
        "kind": "file",
        "sha256": sha256(path),
        "mode": stat.S_IMODE(path.stat().st_mode),
    }


def runtime_sources(root):
    paths = set((root / "server/src").rglob("*.py"))
    paths.update((root / "contracts").rglob("*.json"))
    paths.update(
        path
        for path in (root / "plugin").rglob("*")
        if path.is_file()
        and path.suffix in {".cs", ".csproj", ".props", ".targets"}
        and not {"bin", "obj"} & set(path.relative_to(root / "plugin").parts)
    )
    return {str(path.relative_to(root)) for path in paths}


def same_source(actual, expected):
    # Exported checkouts can use a different umask. Git tracks executability,
    # while selection preserves this working tree's original access permissions.
    return (
        actual is not None
        and all(actual[key] == expected[key] for key in ("kind", "sha256"))
        and (actual["mode"] & 0o111 == expected["mode"] & 0o111)
    )


def assess(trial, run, discovery, reserved):
    """Fail closed on incomplete runs, task regressions or missing reserved evidence."""
    ts, tm = read(trial / "state.json"), read(trial / "manifest.json")
    suite = read(trial / "suite.json")
    expected = {
        name: suite.get("baseline_expectations", {}).get(name, True)
        for name in suite["cases"]
    }
    trial_result = read(trial / "comparison.json")
    if (
        ts["stage"] != "accepted_trial"
        or ts["runtime_dirty"]
        or not ts["candidate_passed"]
        or ts["baseline_cases"] != expected
        or ts["restored_cases"] != expected
        or trial_result["candidate"] != dict.fromkeys(expected, True)
        or sha256(trial / "manifest.json") != ts["manifest_sha256"]
        or sha256(trial / "reviewed.patch") != tm["patch_sha256"]
        or sha256(trial / "suite.json") != tm["suite_sha256"]
        or inventory(trial / "source") != tm["source_inventory"]
    ):
        raise ValueError("Capability trial is not intact and accepted")
    # Original supervisor inputs may evolve after a completed trial. Its archived
    # copies must still match the exact inputs frozen before that trial ran.
    for source, digest in tm["suite_inputs"].items():
        archived = trial / "suite-source" / Path(source).relative_to(ROOT)
        if not archived.is_file() or sha256(archived) != digest:
            raise ValueError("Archived trial inputs are absent or changed")
    comparison.check_pins(run)
    state, contract = read(run / "state.json"), read(run / "contract.json")
    report, plan = read(run / "comparison.json"), read(run / "schedule.json")
    resources = read(run / "resources.json")
    if (
        state["stage"] != "complete"
        or state["runtime_dirty"]
        or contract.get("evaluation_mode") != "trusted_baseline"
        or resources["pending"] is not None
        or resources["stopped"]
        or contract["binaries"]["baseline"]["identity"] != tm["baseline"]
        or contract["binaries"]["candidate"]["identity"] != ts["candidate"]
    ):
        raise ValueError("Comparison is incomplete, dirty or uses different binaries")
    computed = comparison.summarize(state["rows"], plan)
    if (
        computed["status"] != "benefit_observed"
        or computed["tasks"] != report["tasks"]
        or computed["runs"] != report["runs"]
    ):
        raise ValueError("No complete, consistent workflow benefit")
    tasks = computed["tasks"]
    discovery, reserved = set(discovery), set(reserved)
    if (
        not discovery
        or not reserved
        or discovery & reserved
        or not (discovery | reserved) <= set(tasks)
        or len({task["family"] for task in tasks.values()}) < 2
        or any(
            task["candidate"]["passes"] != 2 or task["correctness_regression"]
            for task in tasks.values()
        )
    ):
        raise ValueError(
            "All candidate repeats, reserved tasks and cross-family preservation required"
        )
    for row in state["rows"]:
        child = run / row["id"]
        artifact, evaluation = (
            read(child / "artifact.json"),
            read(child / "evaluation.json"),
        )
        if (
            artifact["evaluation_pending"]
            or sha256(child / "candidate.3dm") != artifact["sha256"]
            or evaluation["artifact_sha256"] != artifact["sha256"]
            or evaluation["status"] != row["task_verdict"]
            or not evaluation["checks"]
            or (evaluation["status"] == "pass") != all(evaluation["checks"].values())
            or evaluation["evaluation_runtime"]["mvid"] != tm["baseline"]["mvid"]
        ):
            raise ValueError("Model or trusted evaluation evidence changed")
    return {
        "kind": "scoped_workflow_benefit",
        "discovery_tasks": sorted(discovery),
        "reserved_tasks": sorted(reserved),
        "benefit_tasks": [
            name for name, task in tasks.items() if task["observed_benefit"]
        ],
        "families_checked": sorted({task["family"] for task in tasks.values()}),
        "trial": str(trial),
        "comparison": str(run),
        "trial_comparison_sha256": sha256(trial / "comparison.json"),
        "workflow_comparison_sha256": sha256(run / "comparison.json"),
    }


def prepare(trial, run, review, discovery, reserved):
    trial, run = trial.resolve(), run.resolve()
    if not review.strip():
        raise ValueError("A scoped supervisor review is required")
    evidence = assess(trial, run, discovery, reserved)
    tm = read(trial / "manifest.json")
    builder = Path(tm["repair"])
    scope, patch = capability.reviewed_source(
        builder, read(builder / "checkpoint.json")
    )
    if patch != (trial / "reviewed.patch").read_bytes():
        raise ValueError("Reviewed capability patch differs from tested patch")
    baseline = read(builder / "baseline_inventory.json")
    names = sorted(scope["create_paths"] + scope["write_paths"])
    with locked(ROOT / "experiments/runs/source-selection.lock"):
        if runtime_sources(ROOT) - set(baseline):
            raise ValueError("Unreviewed production source additions are present")
        # Preserve any unrelated production edits; do not silently incorporate them.
        for name, expected in baseline.items():
            if expected["kind"] == "file" and name.startswith(
                ("plugin/", "server/", "contracts/")
            ):
                if not same_source(file_state(target(ROOT, name)), expected):
                    raise ValueError(
                        "Production source changed since baseline: " + name
                    )
        for name in scope["create_paths"]:
            if file_state(target(ROOT, name)) is not None:
                raise ValueError("New capability target already exists: " + name)
        directory = (
            ROOT
            / "experiments/runs"
            / (time.strftime("selection-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        )
        directory.mkdir()
        entries = {}
        for name in names:
            before, after = target(ROOT, name), trial / "source" / name
            entries[name] = {"before": file_state(before), "after": file_state(after)}
            entries[name]["after"]["mode"] = (
                entries[name]["before"]["mode"]
                if entries[name]["before"] is not None
                else 0o644
            )
            for label, source in [("before", before), ("after", after)]:
                if source.exists():
                    dest = directory / label / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(source.read_bytes())
                    dest.chmod(entries[name][label]["mode"])
        persist(
            directory / "manifest.json",
            {
                "root": str(ROOT),
                "entries": entries,
                "evidence": evidence,
                "review": review,
                "baseline": tm["baseline"],
                "candidate": read(trial / "state.json")["candidate"],
            },
        )
        persist(
            directory / "state.json",
            {
                "stage": "prepared",
                "manifest_sha256": sha256(directory / "manifest.json"),
                "events": [],
                "runtime_verified": False,
            },
        )
        runtime_dir = directory / "runtime"
        runtime_dir.mkdir()
        for arm in ("baseline", "candidate"):
            shutil.copy2(run / (arm + ".rhp"), runtime_dir / (arm + ".rhp"))
        persist(
            runtime_dir / "contract.json",
            {
                "binaries": read(run / "contract.json")["binaries"],
            },
        )
        persist(
            runtime_dir / "state.json",
            {
                "stage": "prepared",
                "runtime_dirty": False,
                "promoted": False,
                "transitions": [],
                "rows": [],
                "contract_sha256": sha256(runtime_dir / "contract.json"),
            },
        )
        return directory


def load(directory):
    state = read(directory / "state.json")
    if sha256(directory / "manifest.json") != state["manifest_sha256"]:
        raise ValueError("Selection manifest changed")
    manifest = read(directory / "manifest.json")
    if Path(manifest["root"]).resolve() != ROOT.resolve():
        raise ValueError("Selection belongs to a different checkout")
    for name, entry in manifest["entries"].items():
        target(ROOT, name)
        for arm in ("before", "after"):
            if file_state(directory / arm / name) != entry[arm]:
                raise ValueError("Selection snapshot changed")
    return manifest, state


def write_snapshot(directory, name, entry, arm):
    path = target(ROOT, name)
    expected = entry[arm]
    if expected is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep an interrupted temporary write inside the journal, outside production.
    temporary = directory / (".write-" + uuid.uuid4().hex)
    try:
        temporary.write_bytes((directory / arm / name).read_bytes())
        temporary.chmod(expected["mode"])
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def change_sources(directory, rollback=False):
    with (
        locked(ROOT / "experiments/runs/rhino.lock"),
        locked(ROOT / "experiments/runs/source-selection.lock"),
    ):
        manifest, state = load(directory)
        allowed = (
            {"applying", "applied", "selected", "rolling_back"}
            if rollback
            else {"prepared", "rolled_back"}
        )
        if state["stage"] not in allowed:
            raise ValueError("Selection is not at a source transition boundary")
        entries = manifest["entries"]
        current = {name: file_state(target(ROOT, name)) for name in entries}
        for name, entry in entries.items():
            acceptable = (
                [entry["before"], entry["after"]] if rollback else [entry["before"]]
            )
            if current[name] not in acceptable:
                raise ValueError("Refuse to overwrite changed source: " + name)
        state.update(
            stage="rolling_back" if rollback else "applying", runtime_verified=False
        )
        state["events"].append({"stage": state["stage"], "time": time.time()})
        persist(directory / "state.json", state)  # Intent survives partial writes.
        arm = "before" if rollback else "after"
        for name, entry in entries.items():
            if file_state(target(ROOT, name)) != current[name]:
                raise ValueError("Source changed during selection: " + name)
            write_snapshot(directory, name, entry, arm)
        state["stage"] = "rolled_back" if rollback else "applied"
        persist(directory / "state.json", state)
        return state


def confirm_runtime(directory):
    from experiments.rhino_trial import runtime

    manifest, state = load(directory)
    arm = "baseline" if state["stage"] == "rolled_back" else "candidate"
    if state["stage"] not in {"rolled_back", "applied"}:
        raise ValueError("No source transition awaits runtime verification")
    source_arm = "before" if arm == "baseline" else "after"
    if any(
        file_state(target(ROOT, name)) != entry[source_arm]
        for name, entry in manifest["entries"].items()
    ):
        raise ValueError("Selected source changed before runtime confirmation")
    observed = runtime()
    if (
        len(observed["docs"]) != 1
        or observed["path"]
        or observed["object_count"]
        or observed["marker"]
        or {"mvid": observed["mvid"], "sha256": sha256(Path(observed["assembly"]))}
        != manifest[arm]
    ):
        raise ValueError("Empty runtime does not match selected sources")
    state.update(runtime_verified=True, runtime=observed)
    if arm == "candidate":
        state["stage"] = "selected"
    persist(directory / "state.json", state)
    return state


def switch_runtime(directory):
    """Issue a supervised lifecycle ticket for the already-selected source state."""
    from experiments import rhino_trial

    with locked(ROOT / "experiments/runs/rhino.lock"):
        manifest, state = load(directory)
        if state["stage"] not in {"applied", "rolled_back"}:
            raise ValueError("Select or roll back sources before switching runtime")
        arm = "candidate" if state["stage"] == "applied" else "baseline"
        runtime_dir = directory / "runtime"
        checkpoint, contract = (
            read(runtime_dir / "state.json"),
            read(runtime_dir / "contract.json"),
        )
        if (
            sha256(runtime_dir / "contract.json") != checkpoint["contract_sha256"]
            or contract["binaries"][arm]["identity"] != manifest[arm]
            or sha256(runtime_dir / (arm + ".rhp")) != manifest[arm]["sha256"]
        ):
            raise ValueError("Runtime selection inputs changed")
        if not (runtime_dir / "runtime-owner.json").exists():
            rhino_trial.claim_empty(runtime_dir)
        comparison.transition(runtime_dir, arm)
        result = confirm_runtime(directory)
        checkpoint = read(runtime_dir / "state.json")
        checkpoint.update(stage="confirmed_" + arm, runtime_dirty=False)
        persist(runtime_dir / "state.json", checkpoint)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    first = commands.add_parser("prepare")
    first.add_argument("trial", type=Path)
    first.add_argument("comparison", type=Path)
    first.add_argument("--review-file", type=Path, required=True)
    first.add_argument("--discovery", action="append", required=True)
    first.add_argument("--reserved", action="append", required=True)
    for action in ("apply", "rollback", "confirm-runtime", "switch-runtime"):
        commands.add_parser(action).add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        print(
            prepare(
                args.trial,
                args.comparison,
                args.review_file.read_text(),
                args.discovery,
                args.reserved,
            )
        )
    elif args.action == "confirm-runtime":
        print(confirm_runtime(args.directory))
    elif args.action == "switch-runtime":
        print(switch_runtime(args.directory))
    else:
        print(change_sources(args.directory, rollback=args.action == "rollback"))
