"""Reviewed new-command builder scope, separate from the edit-only defect route.

Exact additions are declared before dispatch. This is a source integrity gate,
not an execution sandbox; independent development/live checks still follow review.
"""

import ast
import json
from pathlib import PurePosixPath
import re

from experiments.repair import inventory
from experiments.runner import sha256


def validate_scope(scope, baseline):
    if set(scope) != {
        "id",
        "baseline_revision",
        "commands",
        "read_paths",
        "write_paths",
        "create_paths",
        "instructions",
    }:
        raise ValueError("Unexpected capability scope fields")
    if not scope["commands"] or not scope["instructions"].strip():
        raise ValueError("Commands and instructions required")
    for key in ("read_paths", "write_paths", "create_paths"):
        paths = scope[key]
        if not isinstance(paths, list) or len(set(paths)) != len(paths):
            raise ValueError("Scope path lists must be unique")
        for name in paths:
            path = PurePosixPath(name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or str(path) != name
                or not name.startswith(
                    (
                        "plugin/Functions/",
                        "plugin/Serializers/",
                        "server/src/rhinomcp/",
                        "server/tests/",
                        "contracts/",
                    )
                )
                or name not in baseline
                and key != "create_paths"
                and name not in scope["create_paths"]
            ):
                raise ValueError("Unsafe or absent scope path")
    writes, creates, reads = map(
        set, (scope["write_paths"], scope["create_paths"], scope["read_paths"])
    )
    if writes & creates or not (writes | creates) <= reads:
        raise ValueError("Write/create paths must be distinct and readable")
    if any(name in baseline for name in creates):
        raise ValueError("Creation target already exists")
    if any(name not in baseline or baseline[name]["kind"] != "file" for name in writes):
        raise ValueError("Replacement requires an existing file")
    required = {"contracts/protocol.json", "contracts/test_schemas.py"}
    allowed_creates = set()
    for name, handler in scope["commands"].items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or not re.fullmatch(
            r"[A-Z][A-Za-z0-9]*", handler
        ):
            raise ValueError("Invalid command or handler name")
        allowed_creates.update(
            {
                f"server/src/rhinomcp/tools/{name}.py",
                f"plugin/Functions/{handler}.cs",
                f"contracts/commands/{name}.json",
                f"server/tests/test_{name}.py",
            }
        )
    if creates != allowed_creates or writes != required:
        raise ValueError(
            "New commands require declared three-tier files, command tests and protocol/envelope edits"
        )
    return scope


def check_candidate(directory, baseline, scope):
    validate_scope(scope, baseline)
    after = inventory(directory)
    if set(baseline) - set(after):
        raise ValueError("Candidate removed protected entries")
    expected_dirs = set()
    for name in scope["create_paths"]:
        expected_dirs.update(
            str(p)
            for p in PurePosixPath(name).parents
            if str(p) != "." and str(p) not in baseline
        )
    if set(after) - set(baseline) != set(scope["create_paths"]) | expected_dirs:
        raise ValueError("Missing or undeclared additions")
    for name in baseline:
        if baseline[name] != after[name] and (
            name not in scope["write_paths"]
            or baseline[name]["mode"] != after[name]["mode"]
            or after[name]["kind"] != "file"
        ):
            raise ValueError("Candidate changed protected entries or modes")
    for name in scope["create_paths"]:
        if after[name]["kind"] != "file" or after[name]["mode"] & 0o111:
            raise ValueError("New sources must be ordinary nonexecutable files")
    protocol = json.loads((directory / "contracts/protocol.json").read_text())
    commands = protocol["$defs"]["command"]["properties"]["type"]["enum"]
    envelope = ast.parse((directory / "contracts/test_schemas.py").read_text())
    expected = []
    for node in ast.walk(envelope):
        if isinstance(node, ast.FunctionDef) and node.name == "test_protocol_envelope":
            for assignment in ast.walk(node):
                if isinstance(assignment, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "expected_commands"
                    for t in assignment.targets
                ):
                    expected = ast.literal_eval(assignment.value)
    for name, handler in scope["commands"].items():
        if name not in commands or name not in expected:
            raise ValueError("New command missing protocol/envelope coverage")
        schema = json.loads((directory / f"contracts/commands/{name}.json").read_text())
        if (
            schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
        ):
            raise ValueError("New params require a closed object schema")
        wrapper = ast.parse(
            (directory / f"server/src/rhinomcp/tools/{name}.py").read_text()
        )
        functions = [
            n
            for n in wrapper.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
        ]
        if len(functions) != 1 or not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "tool"
            for n in functions[0].decorator_list
        ):
            raise ValueError("Missing native tool registration")
        if not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, (ast.Name, ast.Attribute))
            and (n.func.id if isinstance(n.func, ast.Name) else n.func.attr)
            == "send_command"
            and n.args
            and isinstance(n.args[0], ast.Constant)
            and n.args[0].value == name
            for n in ast.walk(functions[0])
        ):
            raise ValueError("Wrapper missing matching transport command")
        source = (directory / f"plugin/Functions/{handler}.cs").read_text()
        if not re.search(
            r'\[McpCommand\("' + re.escape(name) + r'"(?:\s*,[^\]]*)?\)\]', source
        ):
            raise ValueError("Handler missing matching command registration")
    return {
        "changed": [name for name in after if baseline.get(name) != after[name]],
        "candidate_inventory": after,
        "protocol_complete": True,
        "executed": False,
        "installed": False,
        "promotion_authorized": False,
    }


def load_manifest(path, expected):
    if sha256(path) != expected:
        raise ValueError("Capability manifest changed")
    return json.loads(path.read_text())


def review_patch(candidate, scope):
    import subprocess

    patch = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--binary"], cwd=candidate
    )
    for name in scope["create_paths"]:
        addition = subprocess.run(
            [
                "git",
                "diff",
                "--no-ext-diff",
                "--binary",
                "--no-index",
                "--",
                "/dev/null",
                name,
            ],
            cwd=candidate,
            capture_output=True,
        )
        if addition.returncode != 1:
            raise RuntimeError("Cannot capture new-file review diff")
        patch += addition.stdout
    return patch


def reviewed_source(directory, checkpoint):
    from pathlib import Path

    manifest = load_manifest(directory / "manifest.json", checkpoint["manifest_sha256"])
    if (
        manifest.get("scope_version") != 2
        or Path(manifest["candidate"]).resolve() != (directory / "candidate").resolve()
    ):
        raise ValueError("Invalid declared capability candidate")
    scope = {
        key: manifest[key]
        for key in (
            "id",
            "baseline_revision",
            "commands",
            "read_paths",
            "write_paths",
            "create_paths",
            "instructions",
        )
    }
    baseline = json.loads((directory / "baseline_inventory.json").read_text())
    report = check_candidate(directory / "candidate", baseline, scope)
    if report["candidate_inventory"] != checkpoint["candidate_inventory"]:
        raise ValueError("Capability changed after review checkpoint")
    return scope, review_patch(directory / "candidate", scope)


def dispatch(scope_path, proposal_path, review, timeout=300):
    """Fresh bounded builder; source review only, no build/install/promotion."""
    import subprocess
    import sys
    import time
    import uuid
    from experiments.repair import export_candidate, BUILDER_SCHEMA
    from experiments.runner import ROOT, run_session
    from experiments.trial import persist
    from experiments.workflow.proposals import validate

    proposal = validate(json.loads(proposal_path.read_text()))
    if proposal["kind"] != "new_capability" or not review.strip():
        raise ValueError("Reviewed new-capability proposal required")
    scope = json.loads(scope_path.read_text())
    revision = subprocess.check_output(
        ["git", "rev-parse", scope["baseline_revision"] + "^{commit}"],
        cwd=ROOT,
        text=True,
    ).strip()
    directory = (
        ROOT
        / "experiments/runs"
        / (time.strftime("capability-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    )
    directory.mkdir()
    candidate = directory / "candidate"
    export_candidate(revision, candidate)
    before = inventory(candidate)
    validate_scope(scope, before)
    persist(directory / "baseline_inventory.json", before)
    manifest = {
        **scope,
        "candidate": str(candidate),
        "baseline_revision": revision,
        "proposal_sha256": sha256(proposal_path),
        "scope_version": 2,
        "review": review,
    }
    persist(directory / "manifest.json", manifest)
    digest = sha256(directory / "manifest.json")
    persist(directory / "proposal.json", proposal)
    instructions = (
        "Create the reviewed general RhinoMCP capability using only the declared source gateway. Implement the complete Python/C#/schema command and protocol/envelope coverage. Do not claim developer tests or live geometry checks you cannot run. This role cannot build, install, access hidden evaluations or promote. Return complete only when the entire scoped source change is ready for review.\n"
        + json.dumps(manifest)
        + "\n"
        + json.dumps(proposal)
    )
    config = {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.capability_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(
            f"{k} = {json.dumps(v)}"
            for k, v in {
                "PYTHONPATH": str(ROOT),
                "BUILDER_MANIFEST": str(directory / "manifest.json"),
                "BUILDER_MANIFEST_SHA256": digest,
            }.items()
        )
        + " }",
        **{
            f"tools.{name}.approval_mode": '"approve"'
            for name in ("read_source", "replace_source", "create_source")
        },
    }
    persist(
        directory / "checkpoint.json", {"stage": "building", "manifest_sha256": digest}
    )
    try:
        result = run_session(
            directory / "builder", instructions, BUILDER_SCHEMA, timeout, config
        )
        load_manifest(directory / "manifest.json", digest)
        if result["complete"] is not True:
            raise ValueError("Builder did not complete")
        report = check_candidate(candidate, before, scope)
        patch = review_patch(candidate, scope)
        (directory / "candidate.patch").write_bytes(patch)
        persist(
            directory / "checkpoint.json",
            {
                **report,
                "stage": "candidate_ready_for_review",
                "manifest_sha256": digest,
                "patch_sha256": sha256(directory / "candidate.patch"),
                "builder_claim": result,
            },
        )
    except BaseException as error:
        persist(
            directory / "failure.json",
            {"error": str(error), "executed": False, "installed": False},
        )
        raise
    return directory


def revise(directory, feedback, timeout=240):
    import sys
    import time
    from experiments.runner import ROOT, run_session
    from experiments.repair import BUILDER_SCHEMA
    from experiments.trial import locked, persist, read

    with locked(directory / "writer.lock"):
        checkpoint = read(directory / "checkpoint.json")
        if checkpoint.get("stage") != "candidate_ready_for_review" or checkpoint.get(
            "executed"
        ):
            raise ValueError("Only an unexecuted reviewed capability can be revised")
        scope, _ = reviewed_source(directory, checkpoint)
        manifest = read(directory / "manifest.json")
        digest = checkpoint["manifest_sha256"]
        review = directory / time.strftime("review-%Y%m%d-%H%M%S")
        review.mkdir()
        persist(review / "before.json", checkpoint)
        (review / "before.patch").write_bytes(
            (directory / "candidate.patch").read_bytes()
        )
        (review / "feedback.txt").write_text(feedback)
        env = {
            "PYTHONPATH": str(ROOT),
            "BUILDER_MANIFEST": str(directory / "manifest.json"),
            "BUILDER_MANIFEST_SHA256": digest,
        }
        config = {
            "command": json.dumps(sys.executable),
            "args": json.dumps(["-m", "experiments.capability_mcp"]),
            "cwd": json.dumps(str(ROOT)),
            "required": "true",
            "env": "{ "
            + ", ".join(f"{k} = {json.dumps(v)}" for k, v in env.items())
            + " }",
            **{
                f"tools.{name}.approval_mode": '"approve"'
                for name in ("read_source", "replace_source", "create_source")
            },
        }
        persist(
            directory / "checkpoint.json",
            {"stage": "revising", "manifest_sha256": digest},
        )
        try:
            result = run_session(
                review / "builder",
                "Revise the existing candidate under the unchanged exact capability scope. Read existing files before replacing. You cannot build, install or inspect hidden evaluators. Report unrun tests honestly.\n"
                + json.dumps(manifest)
                + "\nSupervisor review:\n"
                + feedback,
                BUILDER_SCHEMA,
                timeout,
                config,
            )
            load_manifest(directory / "manifest.json", digest)
            if result["complete"] is not True:
                raise ValueError("Builder revision incomplete")
            report = check_candidate(
                directory / "candidate",
                read(directory / "baseline_inventory.json"),
                scope,
            )
            (directory / "candidate.patch").write_bytes(
                review_patch(directory / "candidate", scope)
            )
            persist(
                directory / "checkpoint.json",
                {
                    **report,
                    "stage": "candidate_ready_for_review",
                    "manifest_sha256": digest,
                    "patch_sha256": sha256(directory / "candidate.patch"),
                    "builder_claim": result,
                },
            )
        except BaseException as error:
            persist(
                review / "failure.json",
                {"error": str(error), "executed": False, "installed": False},
            )
            raise
    return review


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("scope", type=Path)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--review-file", type=Path, required=True)
    args = parser.parse_args()
    print(dispatch(args.scope, args.proposal, args.review_file.read_text()))
