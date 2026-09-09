"""Deterministic feasibility check; not an agent-effectiveness comparison."""

import json
import math
from pathlib import Path

from rhinomcp.server import get_rhino_connection
from experiments.bridge import script
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, load_task, save, save_candidate, measure, capture
from experiments.evaluator import evaluate
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from experiments.workflow.pilot import cleanup


def run(directory):
    directory.mkdir()  # Preserve earlier attempts.
    rows = []
    with locked(ROOT / "experiments/runs/rhino.lock"):
        for name in ("panel_raised", "panel_depressed", "unseen_shallow_panel"):
            task = load_task(ROOT / f"experiments/tasks/{name}.json")
            owner = runtime()
            require_owned(owner, owner)
            assert not owner["object_count"] and not owner["marker"]
            before = fingerprint()
            child = directory / name
            child.mkdir()
            marker = directory.name + name
            script(
                f'doc.Strings.SetString("rhinomcp_experiment",{json.dumps(marker)}); doc.ModelUnitSystem=UnitSystem.Millimeters; doc.ModelAbsoluteTolerance={task["linear_tolerance"]};'
            )
            try:
                w, d, _ = task["dimensions"]
                h = task["panel_height"]
                a = math.radians(task["rotation_x_degrees"])
                tx, ty, tz = task["translation"]
                points = []
                for i in range(3):
                    for j in range(3):
                        x, y = w * i / 2, d * j / 2
                        z = h if i == j == 1 else 0
                        points.append(
                            [
                                x + tx,
                                y * math.cos(a) - z * math.sin(a) + ty,
                                y * math.sin(a) + z * math.cos(a) + tz,
                            ]
                        )
                params = {
                    "type": "SURFACE",
                    "params": {
                        "count": [3, 3],
                        "points": points,
                        "degree": [2, 2],
                        "closed": [False, False],
                    },
                }
                save(child / "construction.json", params)
                response = get_rhino_connection().send_command("create_object", params)
                save(child / "response.json", response)
                artifact = child / "candidate.3dm"
                digest = save_candidate(artifact, owner["document"], marker)
                report = evaluate(task, measure(artifact, task))
                report["artifact_sha256"] = digest
                save(child / "evaluation.json", report)
                capture(child, owner["document"], marker)
                rows.append({"task": name, "evaluation": report})
            finally:
                cleanup(owner, marker, before)
        result = {
            "rows": rows,
            "pass": all(r["evaluation"]["status"] == "pass" for r in rows),
            "claim": "Deterministic construction feasibility; no agent transfer claim.",
            "runtime": runtime(),
        }
        save(directory / "result.json", result)
        return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory.resolve())))
