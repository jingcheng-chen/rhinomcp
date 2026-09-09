"""Task-independent, read-only workflow telemetry from recorded agent sessions.

Historical audits identify friction; they cannot establish causal improvement.
No Rhino imports, task geometry, candidate execution or promotion logic.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from experiments.workflow.flaws import trace, report_run, rank


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def summarize_events(path):
    rows, usage, _ = trace(path)
    tools, commands, failed = Counter(), Counter(), Counter()
    for item in rows:
        tool = item["tool"]
        tools[tool] += 1
        if not tool.startswith("describe_") and item["command"] not in {
            "assembly_command",
            "modeling_command",
        }:
            commands[item["command"]] += 1
        if item["failed"]:
            failed[tool] += 1
    return {
        "mcp_attempts": len(rows),
        "completed_calls": sum(r["completed"] for r in rows),
        "unfinished_calls": sum(not r["completed"] for r in rows),
        "failed_calls": sum(failed.values()),
        "failures_by_tool": dict(sorted(failed.items())),
        "tools": dict(sorted(tools.items())),
        "commands": dict(sorted(commands.items())),
        "schema_queries": sum(
            n for tool, n in tools.items() if tool.startswith("describe_")
        ),
        "delete_calls": commands.get("delete_object", 0),
        "usage": usage,
        "caution": "Delete calls may be normal construction cleanup. Call failures may be gateway, input or runtime failures; neither proves a plugin defect.",
    }


def audit_run(root, entry):
    path = (root / entry["run"]).resolve()
    path.relative_to((root / "experiments/runs").resolve())
    events = path / "modeler/events.jsonl"
    if not events.exists():
        return {"id": entry["id"], "family": entry["family"], "available": False}
    stats = summarize_events(events)
    status = read(path / "modeler/status.json") or {}
    evaluation = read(path / "evaluation.json") or {}
    verdict = evaluation.get("status")
    if verdict not in {"pass", "fail"}:
        verdict = "unscored"
    result = read(path / "modeler/result.json") or {}
    return {
        "id": entry["id"],
        "family": entry["family"],
        "available": True,
        "source": entry["run"],
        "source_sha256": digest(events),
        "session_status": status.get("status"),
        "elapsed_seconds": status.get("elapsed_seconds"),
        "task_verdict": verdict,
        "agent_claim_complete": result.get("complete"),
        "evaluation_sha256": digest(path / "evaluation.json") if evaluation else None,
        "result_sha256": digest(path / "modeler/result.json")
        if (path / "modeler/result.json").exists()
        else None,
        "status_sha256": digest(path / "modeler/status.json")
        if (path / "modeler/status.json").exists()
        else None,
        "environment_sha256": digest(path / "environment.json")
        if (path / "environment.json").exists()
        else None,
        "metrics": stats,
        "flaws": report_run(path, entry, evaluation, result),
        "cohort": entry.get("cohort", "unspecified"),
        "environment": read(path / "environment.json"),
        "timing_sha256": digest(path / "calls.jsonl")
        if (path / "calls.jsonl").exists()
        else None,
        "comparison_eligible": False,
        "comparison_blockers": [
            "Historical sessions do not pin a common agent model/version and identical task, evaluator and environment across plugin versions."
        ],
    }


def audit(root, registry):
    entries = registry["runs"]
    if len({e["id"] for e in entries}) != len(entries):
        raise ValueError("Duplicate run ID")
    if len({(root / e["run"]).resolve() for e in entries}) != len(entries):
        raise ValueError("Duplicate run path")
    runs = [audit_run(root, e) for e in entries]
    confirmed = [
        {
            **r,
            "flaws": {
                **r.get("flaws", {}),
                "findings": [
                    f
                    for f in r.get("flaws", {}).get("findings", [])
                    if f["confidence"] in {"observed", "reviewed"}
                ],
            },
        }
        for r in runs
    ]
    return {
        "taxonomy_version": 1,
        "rankings": {
            "overall": rank(runs),
            "observed_or_reviewed_flaws": rank(confirmed),
            "observed_flaws_by_cohort": {
                cohort: rank([r for r in confirmed if r.get("cohort") == cohort])
                for cohort in sorted({r.get("cohort", "unspecified") for r in runs})
            },
            "by_seconds_complete_only": sorted(
                [r for r in rank(confirmed) if r["score_seconds"] is not None],
                key=lambda r: -r["score_seconds"],
            ),
            "by_tool": rank(runs, "tool"),
            "by_family": rank(runs, "family"),
            "by_cohort": {
                cohort: rank([r for r in runs if r.get("cohort") == cohort])
                for cohort in sorted({r.get("cohort", "unspecified") for r in runs})
            },
        },
        "ranking_policy": "Frequency times mean charged calls; seconds reported only with complete timing coverage. Categories overlap and must not be summed. Observation/candidate rows are not confirmed product flaws.",
        "purpose": "Find cross-task workflow friction, not score modeling quality or claim improvement.",
        "families": sorted({r["family"] for r in runs if r["available"]}),
        "runs": runs,
        "promotion_authorized": False,
        "limitation": "Historical heterogeneous observations only. Missing data stays unknown; task success and efficiency are separate.",
    }


def validate_labels(report, labels):
    """Check separately reviewed labels; unavailable evidence never counts as a pass."""
    runs = {r["id"]: r for r in report["runs"]}
    checked, unavailable = [], []
    for label in labels["runs"]:
        run = runs.get(label["id"])
        if run is None or not run["available"]:
            unavailable.append(label["id"])
            continue
        if (
            run["metrics"]["mcp_attempts"] != label["calls"]
            or run["flaws"]["counts"] != label["counts"]
        ):
            raise ValueError(
                "Classifier disagrees with reviewed labels: " + label["id"]
            )
        checked.append(label["id"])
    return {
        "checked": checked,
        "unavailable": unavailable,
        "status": "matched" if not unavailable else "incomplete",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path, nargs="+")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--labels", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = audit(
        root,
        {
            "runs": [
                entry
                for path in args.registry
                for entry in json.loads(path.read_text())["runs"]
            ]
        },
    )
    report["input_hashes"] = {str(p): digest(p) for p in args.registry}
    report["classifier_hashes"] = {
        p.name: digest(p)
        for p in (Path(__file__), Path(__file__).with_name("flaws.py"))
    }
    if args.labels:
        report["validation"] = validate_labels(
            report, json.loads(args.labels.read_text())
        )
        report["input_hashes"][str(args.labels)] = digest(args.labels)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
