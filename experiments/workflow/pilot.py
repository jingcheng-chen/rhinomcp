"""Shared prospective session/evaluation pilot using native production tool schemas."""

import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from experiments.bridge import assert_document, script
from experiments.evaluator import evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import (
    ROOT,
    MODELER_SCHEMA,
    load_task,
    run_session,
    role_instructions,
    save,
    sha256,
    evaluator_versions,
    save_candidate,
    measure,
    capture,
)
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from experiments.workflow.audit import audit
from experiments.workflow.native_mcp import Gateway, TOOLS


def load_suite(path):
    suite = json.loads(path.read_text())
    if set(suite) != {"id", "call_budget", "timeout_seconds", "tasks"}:
        raise ValueError("Unexpected suite fields")
    for key in ("call_budget", "timeout_seconds"):
        if type(suite[key]) is not int or not 0 < suite[key] <= 600:
            raise ValueError("Invalid session budget")
    if not suite["tasks"]:
        raise ValueError("Empty suite")
    for entry in suite["tasks"]:
        if set(entry) != {"family", "path"} or not entry["family"]:
            raise ValueError("Invalid task registration")
        task_path = (ROOT / entry["path"]).resolve()
        task_path.relative_to(ROOT / "experiments/tasks")
        task = load_task(task_path)
        if task["type"] not in {
            "axis_aligned_box",
            "box_through_hole",
            "triangular_prism_pose",
            "biquadratic_panel",
        } or task.get("input_mode"):
            raise ValueError("No pilot evaluator adapter for this task")
    return suite


def source_pins():
    files = list((ROOT / "server/src/rhinomcp").rglob("*.py"))
    files += list((ROOT / "experiments/workflow").glob("*.py"))
    files += [ROOT / "experiments" / name for name in evaluator_versions()]
    files += [
        ROOT / name
        for name in (
            "experiments/runner.py",
            "experiments/bridge.py",
            "experiments/rhino_trial.py",
            "experiments/strip_probe.py",
            "experiments/trial.py",
            "experiments/harness/roles/modeler.md",
        )
    ]
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(set(files))}


def cleanup(owner, marker, before):
    require_owned(runtime(), owner)
    assert_document(owner["document"], marker)
    # This runner claims only empty documents and exposes no layer-writing tools.
    # Hidden construction objects must also be removed.
    script(f"""
var settings=new Rhino.DocObjects.ObjectEnumeratorSettings {{ NormalObjects=true, HiddenObjects=true, LockedObjects=true, ReferenceObjects=true, IncludeLights=true }};
foreach(var obj in doc.Objects.GetObjectList(settings).Where(o=>o!=null && !o.IsDeleted).ToArray())
 if(!doc.Objects.Delete(obj.Id,true)) throw new Exception("Cleanup failed");
doc.ModelUnitSystem=(UnitSystem)Enum.Parse(typeof(UnitSystem),{json.dumps(before["units"])});
doc.ModelAbsoluteTolerance={before["tolerance"]};
doc.Strings.Delete("rhinomcp_experiment");
""")
    after = fingerprint()
    if before != after:
        raise RuntimeError("Pre-existing document state changed")
    return after


def run_task(
    directory, entry, suite, definitions, agent_config=None, description_file=None
):
    task = load_task(ROOT / entry["path"])
    marker = directory.parent.name + "-" + directory.name
    owner = runtime()
    require_owned(owner, owner)
    if owner["object_count"] or owner["marker"]:
        raise RuntimeError("An empty unclaimed dedicated document is required")
    before = fingerprint()
    directory.mkdir()
    print(directory, flush=True)
    pins = source_pins()
    for name in pins:
        p = directory / "sources" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    prompt = task["instruction"] + "\n" + role_instructions("modeler")
    save(directory / "task.json", task)
    save(directory / "tool-definitions.json", definitions)
    save(directory / "pins.json", pins)
    environment = {
        "rhino": owner,
        "plugin_sha256": sha256(Path(owner["assembly"])),
        "codex_version": subprocess.check_output(
            ["codex", "--version"], text=True
        ).strip(),
        "model": agent_config or "CLI default; resolved model version unavailable",
        "comparison_eligible": False,
        "comparison_blockers": [
            "No pinned resolved model version or paired candidate/repeats"
        ],
        "call_budget": suite["call_budget"],
        "timeout_seconds": suite["timeout_seconds"],
    }
    save(directory / "environment.json", environment)
    script(f"""
doc.Strings.SetString("rhinomcp_experiment",{json.dumps(marker)});
doc.ModelUnitSystem=UnitSystem.Millimeters;
doc.ModelAbsoluteTolerance={task["linear_tolerance"]};
""")
    env = {
        "PYTHONPATH": str(ROOT),
        "EXPERIMENT_DOCUMENT": str(owner["document"]),
        "EXPERIMENT_MARKER": marker,
        "EXPERIMENT_MAX_CALLS": str(suite["call_budget"]),
        "EXPERIMENT_CALL_LOG": str(directory / "calls.jsonl"),
    }
    if description_file is not None:
        env["EXPERIMENT_DESCRIPTION_FILE"] = str(description_file)
    config = {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.workflow.native_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{k} = {json.dumps(v)}" for k, v in env.items())
        + " }",
        **{f"tools.{name}.approval_mode": '"approve"' for name in TOOLS},
    }
    try:
        result = run_session(
            directory / "modeler",
            prompt,
            MODELER_SCHEMA,
            suite["timeout_seconds"],
            config,
            agent_config=agent_config,
        )
        if source_pins() != pins:
            raise RuntimeError("Sources changed during modeling")
        current = runtime()
        require_owned(current, owner)
        if (
            current["mvid"] != owner["mvid"]
            or sha256(Path(current["assembly"])) != environment["plugin_sha256"]
        ):
            raise RuntimeError("Plugin identity changed")
        artifact = directory / "candidate.3dm"
        artifact_hash = save_candidate(artifact, owner["document"], marker)
        report = evaluate(task, measure(artifact, task))
        report["artifact_sha256"] = artifact_hash
        save(directory / "evaluation.json", report)
        capture(directory, owner["document"], marker)
        save(
            directory / "summary.json",
            {
                "status": report["status"],
                "modeler": result,
                "promotion_authorized": False,
            },
        )
    except BaseException as error:
        save(
            directory / "failure.json",
            {"error": str(error), "type": type(error).__name__},
        )
        raise
    finally:
        after = cleanup(owner, marker, before)
        save(
            directory / "preservation.json",
            {"before": before, "after": after, "preserved": True},
        )


def run(path, agent_config=None):
    suite = load_suite(path)
    runs = ROOT / "experiments/runs"
    runs.mkdir(exist_ok=True)
    with locked(runs / "rhino.lock"):
        directory = runs / (
            time.strftime("workflow-baseline-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        )
        directory.mkdir()
        save(directory / "suite.json", suite)
        definitions = [
            t.model_dump(mode="json", exclude_none=True)
            for t in asyncio.run(Gateway(0, "", 1, directory / "unused").definitions())
        ]
        registry = {"runs": []}
        for index, entry in enumerate(suite["tasks"]):
            child = directory / f"task-{index + 1}"
            run_task(child, entry, suite, definitions, agent_config=agent_config)
            registry["runs"].append(
                {
                    "id": load_task(ROOT / entry["path"])["id"],
                    "family": entry["family"],
                    "run": str(child.relative_to(ROOT)),
                }
            )
            save(directory / "registry.json", registry)
            save(directory / "audit.json", audit(ROOT, registry))
        return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "suite", type=Path, nargs="?", default=Path(__file__).with_name("pilot.json")
    )
    parser.add_argument("--model")
    parser.add_argument(
        "--reasoning-effort", choices=["low", "medium", "high", "xhigh"]
    )
    args = parser.parse_args()
    if bool(args.model) != bool(args.reasoning_effort):
        parser.error("Provide both --model and --reasoning-effort")
    config = (
        {"model": args.model, "reasoning_effort": args.reasoning_effort}
        if args.model
        else None
    )
    print(run(args.suite, agent_config=config))
