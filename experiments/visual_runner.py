"""Screenshot-only diagnostic baseline; structural checks do not imply visual acceptance."""

import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from experiments.bridge import assert_document, script
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import (
    ROOT,
    MODELER_SCHEMA,
    PLANNER_SCHEMA,
    run_session,
    save,
    sha256,
    save_candidate,
)
from experiments.trial import locked
from experiments.visual_mcp import COMMANDS
from rhinomcp.server import get_rhino_connection


def structural_report(task, measured):
    objects = measured["objects"]
    checks = {
        "nonempty": bool(objects),
        "millimeters": measured["units"] == "Millimeters",
        "all_valid": bool(objects) and all(o["valid"] for o in objects),
        "normalized_width": abs(measured["dimensions"][0] - task["normalized_width"])
        <= task["width_tolerance"],
        "no_construction_curves": bool(objects)
        and all(o["type"] not in {"Curve", "Point"} for o in objects),
    }
    checks.update(
        {
            "named_group/" + prefix: any(o["name"].startswith(prefix) for o in objects)
            for prefix in task["part_prefixes"]
        }
    )
    return {
        "status": "unscored",
        "structural_checks": checks,
        "limitation": "Names verify organization only, not part semantics. Valid geometry is not proof of visual similarity. Cameras and visual thresholds are uncalibrated.",
        "measurements": measured,
    }


def freeze_references(source, destination, views):
    manifest = json.loads((source / "public.json").read_text())
    if set(manifest["views"]) != set(views):
        raise ValueError("Public view set does not match task")
    destination.mkdir()
    for view, meta in manifest["views"].items():
        filename = meta["file"]
        if Path(filename).name != filename or not filename.endswith(".png"):
            raise ValueError("Public reference must be a PNG basename")
        path = source / filename
        if path.is_symlink() or sha256(path) != meta["sha256"]:
            raise ValueError("Reference hash mismatch")
        shutil.copy2(path, destination / filename)
    save(destination / "public.json", manifest)
    return manifest


def pinned_inputs():
    paths = [
        ROOT / "experiments" / name
        for name in (
            "visual_runner.py",
            "visual_mcp.py",
            "visual_audit.cs",
            "runner.py",
            "bridge.py",
            "rhino_trial.py",
        )
    ]
    paths += [
        ROOT / "contracts/commands" / (name + ".json")
        for name in COMMANDS | {"capture_viewport"}
    ]
    paths += [ROOT / "contracts/common/definitions.json"]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def configuration(run, owner, references, budget, readonly=False):
    env = {
        "PYTHONPATH": str(ROOT),
        "EXPERIMENT_DOCUMENT": str(owner["document"]),
        "EXPERIMENT_PID": str(owner["pid"]),
        "EXPERIMENT_MARKER": run.name,
        "EXPERIMENT_MAX_CALLS": str(budget),
        "EXPERIMENT_REFERENCE_DIR": str(references),
        "EXPERIMENT_TOOL_LOG": str(
            run / ("review-tools.jsonl" if readonly else "modeling-tools.jsonl")
        ),
        "EXPERIMENT_READ_ONLY": "1" if readonly else "0",
    }
    allowed = ["get_reference_image", "inspect_view"]
    if not readonly:
        allowed += ["modeling_command", "describe_modeling_command"]
    config = {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.visual_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{k} = {json.dumps(v)}" for k, v in env.items())
        + " }",
    }
    for name in allowed:
        config[f"tools.{name}.approval_mode"] = '"approve"'
    config["disabled_tools"] = json.dumps(
        [] if not readonly else ["modeling_command", "describe_modeling_command"]
    )
    return config


def run(task_path, reference_dir):
    task = json.loads(task_path.read_text())
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        if (
            len(owner["docs"]) != 1
            or owner["object_count"]
            or owner["path"]
            or owner["marker"]
        ):
            raise RuntimeError("Use a dedicated empty unsaved Rhino document")
        directory = (
            ROOT
            / "experiments/runs"
            / (time.strftime("visual-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        )
        directory.mkdir()
        print(directory, flush=True)
        save(directory / "task.json", task)
        references = freeze_references(
            reference_dir, directory / "references", task["public_views"]
        )
        pins = pinned_inputs()
        save(directory / "inputs.json", pins)
        for name in pins:
            dst = directory / "source" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dst)
        save(
            directory / "environment.json",
            {
                "rhino": owner,
                "plugin_sha256": sha256(Path(owner["assembly"])),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "codex_version": subprocess.check_output(
                    ["codex", "--version"], text=True
                ).strip(),
            },
        )
        script(
            f'doc.Strings.SetString("rhinomcp_experiment",{json.dumps(directory.name)}); doc.ModelUnitSystem=UnitSystem.Millimeters; doc.ModelAbsoluteTolerance=0.01;'
        )
        save(
            directory / "checkpoint.json",
            {"stage": "modeling", "owner": owner, "marker": directory.name},
        )
        modeler_error = None
        claim = None
        try:
            claim = run_session(
                directory / "modeler",
                task["instruction"]
                + "\nPublic screenshot names: "
                + json.dumps(task["public_views"])
                + "\nRead every public image before modeling. Use only the provided tools. Read command contracts before calls. Tool budget: "
                + str(task["max_calls"]),
                MODELER_SCHEMA,
                task["timeout_seconds"],
                configuration(
                    directory, owner, directory / "references", task["max_calls"]
                ),
            )
        except Exception as error:
            modeler_error = str(error)
        # Preserve partial geometry after a failed or timed-out modeler; do not replay mutations.
        require_owned(runtime(), owner)
        assert_document(owner["document"], directory.name)
        binary = directory / "candidate.3dm"
        artifact = save_candidate(binary, owner["document"], directory.name)
        if pinned_inputs() != pins:
            raise RuntimeError("Pinned implementation changed during baseline")
        for meta in references["views"].values():
            if sha256(directory / "references" / meta["file"]) != meta["sha256"]:
                raise RuntimeError("Reference changed")
        measured = json.loads(
            script(
                (ROOT / "experiments/visual_audit.cs")
                .read_text()
                .replace("ARTIFACT_PATH", json.dumps(str(binary)))
            )
        )
        if sha256(binary) != artifact:
            raise RuntimeError("Saved model changed during audit")
        report = structural_report(task, measured)
        report["artifact_sha256"] = artifact
        save(directory / "evaluation.json", report)
        # Shaded views are presentation evidence only; saved model has already been audited.
        script(
            "foreach(var view in doc.Views) view.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.ShadedId); doc.Views.Redraw();"
        )
        for view in ("perspective", "front", "right", "back", "top"):
            result = get_rhino_connection().send_command(
                "capture_viewport",
                {
                    "viewport": view,
                    "width": 1000,
                    "height": 750,
                    "show_grid": False,
                    "show_axes": False,
                    "zoom_to_fit": True,
                },
            )
            (directory / (view + ".png")).write_bytes(
                base64.b64decode(result["image_data"])
            )
        save(
            directory / "checkpoint.json",
            {"stage": "reviewing", "artifact_sha256": artifact, "owner": owner},
        )
        review = run_session(
            directory / "planner",
            "You are the independent diagnostic planner. Inspect all public reference images and the candidate in at least perspective, right and back views using the read-only tools. Compare visible form and distinguish modeling choices, missing tools, reproducible plugin failures, and evaluator limitations. This is one benchmark for general tool improvement. Propose a small transferable next experiment and preserve the existing 43-case suite. No calibrated visual pass/fail is available; do not claim acceptance or dispatch a plugin repair merely because geometry is valid. No source mesh or external tools are available.\n"
            + json.dumps(
                {
                    "task": task,
                    "claim": claim,
                    "modeler_error": modeler_error,
                    "audit": report,
                }
            ),
            PLANNER_SCHEMA,
            300,
            configuration(directory, owner, directory / "references", 30, True),
        )
        if pinned_inputs() != pins:
            raise RuntimeError("Pinned implementation changed during review")
        require_owned(runtime(), owner)
        summary = {
            "task": task["id"],
            "evaluation": "unscored",
            "modeler_claim": claim,
            "modeler_error": modeler_error,
            "planner": review,
            "artifact_sha256": artifact,
            "plugin_changed": False,
            "promoted": False,
            "structural_checks": report["structural_checks"],
        }
        save(directory / "summary.json", summary)
        save(
            directory / "checkpoint.json",
            {"stage": "completed_diagnostic", "owner": owner, "marker": directory.name},
        )
        print(json.dumps(summary), flush=True)
        return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("references", type=Path)
    args = parser.parse_args()
    run(args.task, args.references)
