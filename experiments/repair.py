"""Prepare a bounded capture-repair candidate; never execute or install it.

The controller exports production source from a pinned Git revision into a separate
checkout. Fresh planner/builder sessions use narrow tools, not a general shell.
A whole-checkout integrity gate runs before candidate code can be reviewed or built.
"""

import argparse
import fcntl
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import time
import uuid

from experiments.runner import (
    ROOT,
    PLANNER_SCHEMA,
    role_instructions,
    run_session,
    save,
    schema,
    sha256,
)

WRITE_PATHS = [
    "plugin/Functions/CaptureViewport.cs",
    "server/src/rhinomcp/tools/capture_viewport.py",
    "contracts/commands/capture_viewport.json",
]
READ_PATHS = WRITE_PATHS + ["plugin/Functions/_utils.cs"]
BUILDER_SCHEMA = schema(
    {
        "summary": {"type": "string"},
        "complete": {"type": "boolean"},
        "validation_notes": {"type": "string"},
    }
)


def inventory(directory):
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Candidate contains a symlink")
        if not (path.is_file() or path.is_dir()):
            raise ValueError(
                f"Candidate contains an unsupported filesystem entry: {path.relative_to(directory)}"
            )
        result[path.relative_to(directory).as_posix()] = {
            "kind": "file" if path.is_file() else "directory",
            "sha256": sha256(path) if path.is_file() else None,
            "mode": path.stat().st_mode & 0o777,
        }
    return result


def check_candidate(directory, before):
    after = inventory(directory)
    if before.keys() != after.keys():
        raise ValueError("Builder added or removed files")
    changed = [path for path in before if before[path] != after[path]]
    if not changed:
        raise ValueError("Builder produced no changes")
    if set(changed) - set(WRITE_PATHS):
        raise ValueError("Builder changed protected files")
    if any(before[path]["mode"] != after[path]["mode"] for path in changed):
        raise ValueError("Builder changed file modes")
    return changed


def require_plugin_plan(plan):
    if plan["action"] != "plugin_issue":
        raise ValueError(
            f"No builder dispatch for {plan['action']}; supervisory review required"
        )


def export_candidate(revision, target):
    archive = subprocess.check_output(
        ["git", "archive", revision, "plugin", "server", "contracts"], cwd=ROOT
    )
    target.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
        for member in contents:
            parts = PurePosixPath(member.name)
            if (
                parts.is_absolute()
                or ".." in parts.parts
                or not (member.isdir() or member.isfile())
            ):
                raise ValueError("Unsafe source archive entry")
            path = target / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents.extractfile(member).read())
                path.chmod(member.mode & 0o777)
    # This checkout has its own Git metadata and no link to the working repository.
    for command in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=RhinoMCP harness",
            "-c",
            "user.email=harness@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "Pinned production baseline",
        ],
    ):
        subprocess.run(["git", *command], cwd=target, check=True, capture_output=True)


def builder_config(directory):
    env = {
        "PYTHONPATH": str(ROOT),
        "BUILDER_MANIFEST": str(directory / "manifest.json"),
    }
    return {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.builder_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{key} = {json.dumps(value)}" for key, value in env.items())
        + " }",
        "tools.read_source.approval_mode": '"approve"',
        "tools.replace_source.approval_mode": '"approve"',
    }


def finish_candidate(directory, result):
    candidate = directory / "candidate"
    before = json.loads((directory / "baseline_inventory.json").read_text())
    if not result["complete"]:
        raise ValueError("Builder reported incomplete work")
    changed = check_candidate(candidate, before)
    patch = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--binary"], cwd=candidate
    )
    (directory / "candidate.patch").write_bytes(patch)
    report = {
        "stage": "candidate_ready_for_review",
        "changed_paths": changed,
        "patch_sha256": sha256(directory / "candidate.patch"),
        "builder_claim": result,
        "executed": False,
        "installed": False,
        "candidate_inventory": inventory(candidate),
    }
    save(directory / "checkpoint.json", report)


def pilot(
    evidence_path, timeout=180, baseline_mvid="243974ba-3378-4df8-88b6-fd4dba066ebc"
):
    evidence = json.loads(evidence_path.read_text())
    # The replay is deliberately pinned to the previously measured capture defect.
    revision = subprocess.check_output(
        ["git", "rev-parse", "a7bd5d1^{commit}"], cwd=ROOT, text=True
    ).strip()
    if evidence.get("environment", {}).get("mvid") != baseline_mvid:
        raise ValueError(
            "Capture pilot requires the recorded baseline assembly evidence"
        )
    cases = evidence["cases"]
    if not any(
        c.get("framing_required") and not c.get("framed") for c in cases.values()
    ):
        raise ValueError("No reproduced framing failure")
    if not any(c.get("state_preserved") is False for c in cases.values()):
        raise ValueError("No reproduced state-preservation failure")
    directory = (
        ROOT
        / "experiments/runs"
        / ("repair-" + time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    )
    directory.mkdir()
    candidate = directory / "candidate"
    export_candidate(revision, candidate)
    before = inventory(candidate)
    save(directory / "baseline_inventory.json", before)
    manifest = {
        "baseline_revision": revision,
        "baseline_mvid": baseline_mvid,
        "candidate": str(candidate.resolve()),
        "read_paths": READ_PATHS,
        "write_paths": WRITE_PATHS,
        "evidence_sha256": sha256(evidence_path),
        "acceptance": "All 11 fixed capture cases pass, all 26 geometry fixtures retain expected verdicts, fresh prism loop passes, loaded binary identity verified. No automatic promotion.",
    }
    save(directory / "manifest.json", manifest)
    save(directory / "baseline_evidence.json", evidence)
    facts = {
        "issue": "A valid saved prism is clipped at requested image aspects; camera state changes after capture.",
        "baseline_revision": revision,
        "cases": {
            name: {k: v for k, v in case.items() if k not in ("before", "after")}
            for name, case in cases.items()
        },
        "scope": WRITE_PATHS,
        "preserve": "Unchanged saved geometry, output PNG dimensions/flags, every viewport camera/target/projection/name, no evaluator changes.",
    }
    save(directory / "development_evidence.json", facts)
    try:
        save(directory / "checkpoint.json", {"stage": "planning"})
        plan = run_session(
            directory / "planner",
            role_instructions("planner")
            + "\nThis is a known-defect replay; diagnose the capture failures.\n"
            + json.dumps(facts),
            PLANNER_SCHEMA,
            timeout,
        )
        require_plugin_plan(plan)
        save(directory / "checkpoint.json", {"stage": "building"})
        config = builder_config(directory)
        result = run_session(
            directory / "builder",
            role_instructions("builder")
            + "\n"
            + json.dumps(
                {
                    "plan": plan,
                    "development_evidence": facts,
                    "read_paths": READ_PATHS,
                    "write_paths": WRITE_PATHS,
                }
            ),
            BUILDER_SCHEMA,
            timeout,
            config,
        )
        finish_candidate(directory, result)
        return directory
    except BaseException as error:
        save(
            directory / "failure.json",
            {
                "error": str(error),
                "type": type(error).__name__,
                "executed": False,
                "installed": False,
            },
        )
        raise


def revise(directory, feedback, timeout=180):
    with (directory / "writer.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return revise_locked(directory, feedback, timeout)


def revise_locked(directory, feedback, timeout):
    checkpoint = json.loads((directory / "checkpoint.json").read_text())
    if checkpoint.get("stage") != "candidate_ready_for_review" or checkpoint.get(
        "executed"
    ):
        raise ValueError("Only an unexecuted, reviewed candidate can be revised")
    manifest = json.loads((directory / "manifest.json").read_text())
    if (
        Path(manifest["candidate"]).resolve() != (directory / "candidate").resolve()
        or manifest["write_paths"] != WRITE_PATHS
        or manifest["read_paths"] != READ_PATHS
    ):
        raise ValueError("Review manifest does not match the fixed builder scope")
    # Verify the candidate still matches the last recorded patch before another writer.
    patch = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--binary"], cwd=directory / "candidate"
    )
    import hashlib

    if hashlib.sha256(patch).hexdigest() != checkpoint["patch_sha256"]:
        raise ValueError("Candidate changed since review")
    check_candidate(
        directory / "candidate",
        json.loads((directory / "baseline_inventory.json").read_text()),
    )
    name = "builder-review-" + uuid.uuid4().hex[:8]
    (directory / (name + "-input.patch")).write_bytes(patch)
    save(directory / (name + "-feedback.json"), {"feedback": feedback})
    save(directory / "checkpoint.json", {"stage": "revising", "session": name})
    try:
        result = run_session(
            directory / name,
            role_instructions("builder")
            + "\nController review:\n"
            + feedback
            + "\n"
            + json.dumps({"read_paths": READ_PATHS, "write_paths": WRITE_PATHS}),
            BUILDER_SCHEMA,
            timeout,
            builder_config(directory),
        )
        finish_candidate(directory, result)
    except BaseException as error:
        save(
            directory / "review_failure.json",
            {"error": str(error), "session": name, "executed": False},
        )
        raise
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--evidence", type=Path)
    source.add_argument("--revise", type=Path)
    parser.add_argument(
        "--feedback", type=Path, help="Controller review text for --revise"
    )
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--baseline-mvid",
        default="243974ba-3378-4df8-88b6-fd4dba066ebc",
        help="Operator-verified MVID when rebuilding the pinned baseline on another host",
    )
    args = parser.parse_args()
    if args.revise:
        if not args.feedback:
            parser.error("--revise requires --feedback")
        print(revise(args.revise.resolve(), args.feedback.read_text(), args.timeout))
    else:
        print(pilot(args.evidence.resolve(), args.timeout, args.baseline_mvid))
