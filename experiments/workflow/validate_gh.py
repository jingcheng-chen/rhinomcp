"""Calibrate the shared GH adapter with supervisor-built definitions and bad snapshots."""

import copy
import json
import time
from pathlib import Path
from experiments.runner import ROOT, save, sha256, load_task
from experiments.bridge import script
from experiments.rhino_trial import runtime
from experiments.strip_probe import fingerprint
from experiments.workflow.pilot import cleanup
from experiments.workflow import gh_ownership as gh
from experiments import gh_task
from experiments.trial import locked


def variants(good):
    yield "correct", copy.deepcopy(good), True
    for name in [
        "solution_error",
        "missing_wire",
        "orphan",
        "wrong_count",
        "wrong_value",
        "truncated",
        "wrong_graph",
        "duplicate_nickname",
    ]:
        s = copy.deepcopy(good)
        first = next(iter(s["outputs"].values()))
        if name == "solution_error":
            s["solution"].update(success=False, error_count=1)
        elif name == "missing_wire":
            for node in s["canvas"]["components"]:
                for port in node["inputs"]:
                    if port.get("sources"):
                        port["sources"] = []
        elif name == "orphan":
            s["canvas"]["components"].append(
                {
                    "instance_id": "extra",
                    "name": "Series",
                    "nickname": "extra",
                    "inputs": [],
                    "outputs": [],
                }
            )
            s["graph"]["components"].append(s["canvas"]["components"][-1])
            s["canvas"]["object_count"] += 1
            s["document"]["object_count"] += 1
        elif name == "wrong_count":
            first["data_count"] += 1
        elif name == "wrong_value":
            first["values"][0]["items"][0] = "bad"
        elif name == "truncated":
            first["truncated"] = True
        elif name == "wrong_graph":
            s["graph"]["graph_id"] = "other"
        elif name == "duplicate_nickname":
            s["canvas"]["components"][0]["nickname"] = s["canvas"]["components"][-1][
                "nickname"
            ]
        yield name, s, False


def run(builds_path=ROOT / "experiments/workflow/gh-calibration-builds.json"):
    directory = (
        ROOT / "experiments/runs" / time.strftime("gh-calibration-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    rows = []
    with locked(ROOT / "experiments/runs/rhino.lock"):
        for f in json.loads(builds_path.read_text()):
            task = load_task(ROOT / f["task"])
            owner = runtime()
            before = fingerprint()
            marker = directory.name + "-" + task["id"]
            if owner["object_count"] or owner["marker"]:
                raise RuntimeError("Empty Rhino required")
            script(
                f'doc.Strings.SetString("rhinomcp_experiment",{json.dumps(marker)});'
            )
            document_id = None
            child = directory / task["id"]
            child.mkdir()
            save(child / "task.json", task)
            try:
                document_id = gh.claim(owner["document"], marker)
                save(child / "build.json", gh.command("gh_build_graph", f["build"]))
                good = gh_task.snapshot(task, owner["document"], marker, document_id)
                gh_task.capture(child, owner["document"], marker, document_id)
                for name, s, expected in variants(good):
                    artifact = child / (name + ".gh.json")
                    save(artifact, s)
                    report = gh_task.evaluate(task, json.loads(artifact.read_text()))
                    save(child / (name + "-evaluation.json"), report)
                    rows.append(
                        {
                            "task": task["id"],
                            "variant": name,
                            "expected_pass": expected,
                            "actual": report["status"],
                            "matched": (report["status"] == "pass") == expected,
                            "failed": report["failed"],
                            "artifact": str(artifact.relative_to(ROOT)),
                            "sha256": sha256(artifact),
                        }
                    )
                # A real changed input, re-solved and independently read back.
                value = f["build"]["values"][1]
                gh.command(
                    "gh_set_parameter_value",
                    {
                        "nickname": value["target"],
                        "input_index": value["input_index"],
                        "value": [-n for n in value["value"]]
                        if isinstance(value["value"], list)
                        else value["value"] + 7,
                    },
                )
                bad = gh_task.snapshot(task, owner["document"], marker, document_id)
                artifact = child / "live-wrong-value.gh.json"
                save(artifact, bad)
                report = gh_task.evaluate(task, json.loads(artifact.read_text()))
                save(child / "live-wrong-value-evaluation.json", report)
                rows.append(
                    {
                        "task": task["id"],
                        "variant": "live-wrong-value",
                        "expected_pass": False,
                        "actual": report["status"],
                        "matched": report["status"] == "fail",
                        "failed": report["failed"],
                        "artifact": str(artifact.relative_to(ROOT)),
                        "sha256": sha256(artifact),
                    }
                )
            finally:
                if document_id:
                    save(
                        child / "gh-cleanup.json",
                        gh.cleanup(owner["document"], marker, document_id),
                    )
                save(
                    child / "preservation.json",
                    {"preserved": cleanup(owner, marker, before) == before},
                )
    result = {
        "directory": str(directory.relative_to(ROOT)),
        "rows": rows,
        "all_matched": all(r["matched"] for r in rows),
        "builds_sha256": sha256(builds_path),
    }
    save(directory / "report.json", result)
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    run()
