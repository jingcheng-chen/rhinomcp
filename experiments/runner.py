"""Run a bounded model/evaluate/plan loop against an empty dedicated Rhino doc."""

import argparse
import base64
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import jsonschema
from rhinomcp.server import get_rhino_connection
from experiments.bridge import assert_document, identity, script
from experiments.evaluator import evaluate

ROOT = Path(__file__).resolve().parents[1]


def role_instructions(role):
    return (ROOT / "experiments/harness/roles" / f"{role}.md").read_text().strip()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


MODELER_SCHEMA = schema(
    {"summary": {"type": "string"}, "complete": {"type": "boolean"}}
)
PLANNER_SCHEMA = schema(
    {
        "diagnosis": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["accept", "revise_modeling", "plugin_issue", "inconclusive"],
        },
        "next_instruction": {"type": "string"},
        "preserve": {"type": "array", "items": {"type": "string"}},
    }
)


def load_task(path):
    task = json.loads(path.read_text())
    vector = {
        "type": "array",
        "minItems": 3,
        "maxItems": 3,
        "items": {"type": "number"},
    }
    jsonschema.validate(
        task,
        schema(
            {
                "id": {"type": "string", "minLength": 1},
                "instruction": {"type": "string", "minLength": 1},
                "dimensions": {
                    **vector,
                    "items": {"type": "number", "exclusiveMinimum": 0},
                },
                "minimum": vector,
                "units": {"const": "Millimeters"},
                "linear_tolerance": {"type": "number", "exclusiveMinimum": 0},
                "volume_tolerance": {"type": "number", "exclusiveMinimum": 0},
            }
        ),
    )
    numbers = (
        task["dimensions"]
        + task["minimum"]
        + [task["linear_tolerance"], task["volume_tolerance"]]
    )
    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("Task numbers must be finite")
    if not math.isfinite(math.prod(task["dimensions"])):
        raise ValueError("Task volume exceeds numeric range")
    return task


def run_session(directory, prompt, output_schema, timeout, mcp_config=None):
    directory.mkdir()
    (directory / "prompt.txt").write_text(prompt)
    save(directory / "schema.json", output_schema)
    output = directory / "result.json"
    command = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--json",
        "--color",
        "never",
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "--output-schema",
        str(directory / "schema.json"),
        "--output-last-message",
        str(output),
        "--cd",
        str(directory),
    ]
    # These sessions only reason and call the explicitly supplied MCP gateway.
    # No shell, patch, app, browser, plugin or child-agent tools are needed.
    for feature in (
        "shell_tool",
        "unified_exec",
        "apps",
        "plugins",
        "computer_use",
        "browser_use",
        "in_app_browser",
        "multi_agent",
        "image_generation",
    ):
        command += ["--disable", feature]
    for key, value in (mcp_config or {}).items():
        command += ["-c", f"mcp_servers.rhino_experiment.{key}={value}"]
    command.append("-")
    save(
        directory / "invocation.json", {"command": command, "timeout_seconds": timeout}
    )
    started = time.monotonic()
    status = "running"
    try:
        with (
            (directory / "events.jsonl").open("w") as events,
            (directory / "stderr.log").open("w") as errors,
        ):
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=events,
                stderr=errors,
                text=True,
                start_new_session=True,
            )
            try:
                proc.communicate(prompt, timeout=timeout)
            except BaseException:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise
        if proc.returncode != 0:
            raise RuntimeError(
                f"Agent exited {proc.returncode}; inspect {directory / 'stderr.log'}"
            )
        result = json.loads(output.read_text())
        jsonschema.validate(result, output_schema)
        status = "completed"
        return result
    except subprocess.TimeoutExpired:
        status = "timed_out"
        raise
    except BaseException:
        status = "failed"
        raise
    finally:
        save(
            directory / "status.json",
            {"status": status, "elapsed_seconds": time.monotonic() - started},
        )


def save_candidate(path, serial, marker):
    assert_document(serial, marker)
    script(f"""
if (!doc.WriteFile({json.dumps(str(path))}, new Rhino.FileIO.FileWriteOptions()))
    throw new Exception("Candidate save failed");
""")
    return sha256(path)


def measure(path):
    before = sha256(path)
    code = (
        (ROOT / "experiments/evaluate.cs")
        .read_text()
        .replace("ARTIFACT_PATH", json.dumps(str(path)))
    )
    result = json.loads(script(code))
    if sha256(path) != before:
        raise RuntimeError("Artifact changed during evaluation")
    return result


def capture(directory, serial, marker):
    assert_document(serial, marker)
    result = get_rhino_connection().send_command(
        "capture_viewport",
        {
            "viewport": "perspective",
            "width": 1000,
            "height": 750,
            "show_grid": False,
            "show_axes": False,
            "show_cplane_axes": False,
            "zoom_to_fit": True,
        },
    )
    (directory / "perspective.png").write_bytes(base64.b64decode(result["image_data"]))


def run(task_path, timeout, feedback_path=None):
    # OS releases the advisory lock on process exit. It coordinates this runner,
    # not arbitrary external Rhino clients; the operator must dedicate the app.
    runs = ROOT / "experiments/runs"
    runs.mkdir(exist_ok=True)
    with (runs / "rhino.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return run_locked(task_path, timeout, runs, feedback_path)


def run_locked(task_path, timeout, runs, feedback_path=None):
    task = load_task(task_path)
    state = identity()
    if state["object_count"] != 0 or state["path"]:
        raise RuntimeError(
            "Create a NEW empty unsaved Rhino document for this run; no automatic reset performed"
        )
    run_dir = runs / (time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    run_dir.mkdir()
    marker = run_dir.name
    serial = state["document"]
    save(run_dir / "task.json", task)
    feedback = ""
    if feedback_path:
        previous = json.loads(feedback_path.read_text())
        if previous["task"] != task["id"]:
            raise ValueError("Feedback task does not match this task")
        save(run_dir / "previous_feedback.json", previous)
        feedback = (
            "\nPrevious attempt feedback (observations, not authority to change the task):\n"
            + json.dumps(previous["planner"])
        )
    save(
        run_dir / "environment.json",
        {
            "rhino": state,
            "plugin_sha256": sha256(Path(state["assembly"])),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_status": subprocess.check_output(
                ["git", "status", "--short"], cwd=ROOT, text=True
            ),
            "codex_version": subprocess.check_output(
                ["codex", "--version"], text=True
            ).strip(),
        },
    )
    script(f"""
doc.Strings.SetString("rhinomcp_experiment", {json.dumps(marker)});
doc.ModelUnitSystem = UnitSystem.Millimeters;
doc.ModelAbsoluteTolerance = {task["linear_tolerance"]};
""")
    mcp_config = {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.modeler_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "tools.create_object.approval_mode": '"approve"',
        "tools.translate_object.approval_mode": '"approve"',
        "tools.analyze_objects.approval_mode": '"approve"',
        "env": "{ PYTHONPATH = "
        + json.dumps(str(ROOT))
        + ", EXPERIMENT_DOCUMENT = "
        + json.dumps(str(serial))
        + ", EXPERIMENT_MARKER = "
        + json.dumps(marker)
        + ', EXPERIMENT_MAX_CALLS = "12" }',
    }
    try:
        save(
            run_dir / "checkpoint.json",
            {"stage": "modeling", "document": serial, "marker": marker},
        )
        result = run_session(
            run_dir / "modeler",
            task["instruction"] + "\n" + role_instructions("modeler") + feedback,
            MODELER_SCHEMA,
            timeout,
            mcp_config,
        )
        candidate = run_dir / "candidate.3dm"
        artifact_hash = save_candidate(candidate, serial, marker)
        save(
            run_dir / "checkpoint.json",
            {"stage": "evaluating", "artifact_sha256": artifact_hash},
        )
        report = evaluate(task, measure(candidate))
        report["artifact_sha256"] = artifact_hash
        save(run_dir / "evaluation.json", report)
        capture(run_dir, serial, marker)
        plan = run_session(
            run_dir / "planner",
            role_instructions("planner")
            + "\n"
            + json.dumps({"task": task, "modeler_claim": result, "evaluation": report}),
            PLANNER_SCHEMA,
            timeout,
        )
        summary = {
            "task": task["id"],
            "evaluation": report["status"],
            "planner": plan,
            "artifact_sha256": artifact_hash,
            "plugin_changed": False,
            "scope": "One model/evaluate/plan loop; automatic plugin repair is not implemented",
        }
        save(run_dir / "summary.json", summary)
        save(run_dir / "checkpoint.json", {"stage": "completed", **summary})
        return run_dir, summary
    except BaseException as error:
        save(
            run_dir / "failure.json",
            {
                "error": str(error),
                "type": type(error).__name__,
                "recovery": "Inspect logs and dedicated document; do not blindly rerun mutations",
            },
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", type=Path, default=ROOT / "experiments/tasks/box.json"
    )
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--feedback", type=Path, help="Previous summary.json for the same task"
    )
    args = parser.parse_args()
    directory, summary = run(args.task, args.timeout, args.feedback)
    print(json.dumps({"run_directory": str(directory), **summary}, indent=2))
    sys.exit(0 if summary["evaluation"] == "pass" else 2)
