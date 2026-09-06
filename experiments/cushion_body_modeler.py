"""Fresh agent builds the fixed continuous cushion top; independent saved-file judge."""

import json
import sys
import time
import uuid

from experiments.bridge import script, assert_document
from experiments.cushion_body_probe import evaluate, measure
from experiments.cushion_body_mcp import COMMANDS
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import (
    ROOT,
    save,
    sha256,
    run_session,
    MODELER_SCHEMA,
    PLANNER_SCHEMA,
    role_instructions,
    save_candidate,
    capture,
)
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def configuration(directory, owner):
    env = {
        "PYTHONPATH": str(ROOT),
        "EXPERIMENT_DOCUMENT": str(owner["document"]),
        "EXPERIMENT_PID": str(owner["pid"]),
        "EXPERIMENT_MARKER": directory.name,
        "EXPERIMENT_MAX_CALLS": "60",
        "EXPERIMENT_TOOL_LOG": str(directory / "tools.jsonl"),
    }
    return {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.cushion_body_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{key} = {json.dumps(value)}" for key, value in env.items())
        + " }",
        "tools.describe_command.approval_mode": '"approve"',
        "tools.join_surfaces.approval_mode": '"approve"',
        "tools.assembly_command.approval_mode": '"approve"',
    }


def run(scale=1.0):
    from experiments.cushion_body_probe import scale_value

    scale_value(scale)
    task = json.loads((ROOT / "experiments/cushion_body_task.json").read_text())
    prompt = task["instruction"] + f"\nUse S={scale}."
    root = "Cushion"
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Use the dedicated empty unsaved document")
        before = fingerprint()
        if before["units"] != "Millimeters":
            raise RuntimeError("Assembly task requires millimeter document units")
        original_ids = {layer["Id"] for layer in before["layers"]}
        if any(layer["Name"] == root for layer in before["layers"]):
            raise RuntimeError(f"Existing {root} layer conflicts with task")
        directory = (
            ROOT
            / "experiments/runs"
            / (
                time.strftime("cushion-body-model-%Y%m%d-%H%M%S-")
                + uuid.uuid4().hex[:8]
            )
        )
        directory.mkdir()
        print(directory, flush=True)
        names = [
            "experiments/cushion_body_modeler.py",
            "experiments/cushion_body_mcp.py",
            "experiments/cushion_body_probe.py",
            "experiments/cushion_body_measure.cs",
            "contracts/commands/run_command.json",
            "experiments/cushion_body_task.json",
            "experiments/layer_modeler_mcp.py",
            "experiments/cushion_probe.py",
            "experiments/cushion_measure.cs",
            "experiments/layer_probe.py",
            "experiments/runner.py",
            "experiments/model_screenshots.py",
            "experiments/bridge.py",
            "experiments/rhino_trial.py",
            "experiments/visual_mcp.py",
            "experiments/strip_probe.py",
            "experiments/harness/roles/modeler.md",
            "experiments/harness/roles/planner.md",
            "contracts/common/definitions.json",
        ] + ["contracts/commands/" + command + ".json" for command in sorted(COMMANDS)]
        pins = {name: sha256(ROOT / name) for name in names}
        save(directory / "inputs.json", pins)
        save(
            directory / "environment.json",
            {**owner, "binary_sha256": sha256(ROOT / owner["assembly"])},
        )
        save(
            directory / "task.json",
            {
                "instruction": prompt,
                "root": root,
                "specification": task,
                "ignored_existing_layer_ids": sorted(original_ids),
            },
        )
        for name in names:
            target = directory / "source" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        script(
            f'doc.Strings.SetString("rhinomcp_experiment",{json.dumps(directory.name)});'
        )
        try:
            result = run_session(
                directory / "modeler",
                role_instructions("modeler") + "\n" + prompt,
                MODELER_SCHEMA,
                360,
                configuration(directory, owner),
            )
            artifact = directory / "candidate.3dm"
            save_candidate(artifact, owner["document"], directory.name)
            first, second = measure(artifact, scale), measure(artifact, scale)
            report = evaluate(
                {
                    **first,
                    "layers": [
                        layer
                        for layer in first["layers"]
                        if layer["id"] not in original_ids
                    ],
                },
                scale,
            )
            report.update(
                repeat_identical=first == second,
                artifact_sha256=sha256(artifact),
                full_measurements=first,
            )
            if first != second:
                raise RuntimeError("Measurements changed on repeat")
            save(directory / "evaluation.json", report)
            capture(directory, owner["document"], directory.name)
            from experiments.model_screenshots import capture_shaded

            capture_shaded(directory, owner["document"], directory.name)
            planner = run_session(
                directory / "planner",
                role_instructions("planner")
                + "\n"
                + json.dumps({"task": prompt, "modeler": result, "evaluation": report}),
                PLANNER_SCHEMA,
                180,
            )
            save(
                directory / "summary.json",
                {
                    "status": report["status"],
                    "modeler": result,
                    "planner": planner,
                    "runtime": owner,
                    "artifact_sha256": report["artifact_sha256"],
                },
            )
        finally:
            require_owned(runtime(), owner)
            assert_document(owner["document"], directory.name)
            ids = ",".join(
                "new Guid(" + json.dumps(value) + ")" for value in original_ids
            )
            script(f"""
foreach(var obj in doc.Objects.Where(o=>o!=null && !o.IsDeleted).ToArray()) doc.Objects.Delete(obj.Id,true);
var oldIds=new HashSet<Guid>(new[]{{{ids}}});
foreach(var layer in doc.Layers.Where(l=>!l.IsDeleted && !oldIds.Contains(l.Id)).OrderByDescending(l=>l.FullPath.Split(new[]{{"::"}},StringSplitOptions.None).Length).ToArray())
 if(!doc.Layers.Delete(layer.Index,true)) throw new Exception("Layer cleanup failed");
doc.Strings.Delete("rhinomcp_experiment");
""")
            after = fingerprint()
            save(
                directory / "preservation.json",
                {"before": before, "after": after, "preserved": before == after},
            )
            if before != after:
                raise RuntimeError("Pre-existing document state changed")
        if pins != {name: sha256(ROOT / name) for name in names}:
            raise RuntimeError("Inputs changed during session")
        print(directory, flush=True)
        return directory


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    run(parser.parse_args().scale)
