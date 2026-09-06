"""Fresh agent builds a public assembly task; supervisor judges the saved layer tree."""

import json
import argparse
from pathlib import Path
import sys
import time
import uuid

from experiments.bridge import script, assert_document
from experiments.layer_probe import evaluate, measure
from experiments.layer_modeler_mcp import COMMANDS
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

TASK = """Build a small assembly in millimeters. Exactly two visible, unlocked, valid solid cubes, each 10 mm on each side. left_part spans world (0,0,0) to (10,10,10); right_part spans (30,0,0) to (40,10,10). Create the layer tree Assembly::Left::Part and Assembly::Right::Part. Put left_part on the first Part layer and right_part on the second. Both leaves must be named Part under their respective parents. All five assembly layers must be visible and unlocked. Do not leave extra objects or extra assembly layers. Existing empty document layers are outside this task; preserve them. Inspect the resulting attributes and report honestly. The supervisor will save and independently evaluate the model. You cannot read or modify the judge. Read command schemas before using tools. Full paths are available for disambiguation."""


def configuration(directory, owner):
    env = {
        "PYTHONPATH": str(ROOT),
        "EXPERIMENT_DOCUMENT": str(owner["document"]),
        "EXPERIMENT_PID": str(owner["pid"]),
        "EXPERIMENT_MARKER": directory.name,
        "EXPERIMENT_MAX_CALLS": "40",
        "EXPERIMENT_TOOL_LOG": str(directory / "tools.jsonl"),
    }
    return {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.layer_modeler_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{key} = {json.dumps(value)}" for key, value in env.items())
        + " }",
        "tools.describe_command.approval_mode": '"approve"',
        "tools.assembly_command.approval_mode": '"approve"',
    }


def run(task_path=None):
    from experiments.assembly_task import load, instruction

    task = load(task_path) if task_path else None
    prompt = instruction(task) if task else TASK
    root = task["root"] if task else "Assembly"
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
            / (time.strftime("layer-model-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        )
        directory.mkdir()
        print(directory, flush=True)
        names = [
            "experiments/layer_modeler.py",
            "experiments/assembly_task.py",
            "experiments/assembly_tasks/schema.json",
            "experiments/layer_modeler_mcp.py",
            "experiments/layer_probe.py",
            "experiments/layer_measure.cs",
            "experiments/runner.py",
            "experiments/bridge.py",
            "experiments/rhino_trial.py",
            "experiments/visual_mcp.py",
            "experiments/strip_probe.py",
            "experiments/harness/roles/modeler.md",
            "experiments/harness/roles/planner.md",
            "contracts/common/definitions.json",
        ] + ["contracts/commands/" + command + ".json" for command in sorted(COMMANDS)]
        if task_path:
            names.append(str(task_path.resolve().relative_to(ROOT)))
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
                240,
                configuration(directory, owner),
            )
            artifact = directory / "candidate.3dm"
            save_candidate(artifact, owner["document"], directory.name)
            first, second = measure(artifact), measure(artifact)
            report = evaluate(
                {
                    **first,
                    "layers": [
                        layer
                        for layer in first["layers"]
                        if layer["id"] not in original_ids
                    ],
                },
                task=task,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path)
    run(parser.parse_args().task)
