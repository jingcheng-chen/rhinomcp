"""Task-independent, read-only workflow telemetry from recorded agent sessions.

Historical audits identify friction; they cannot establish causal improvement.
No Rhino imports, task geometry, candidate execution or promotion logic.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def summarize_events(path):
    started, completed = {}, {}
    usage = None
    with path.open() as stream:
        for line in stream:
            event = json.loads(line)
            if event.get("type") == "turn.completed":
                usage = event.get("usage")  # Never infer missing usage as zero.
            item = event.get("item", {})
            if item.get("type") != "mcp_tool_call":
                continue
            if event["type"] == "item.started":
                started[item["id"]] = item
            elif event["type"] == "item.completed":
                completed[item["id"]] = item
    tools, commands, failed = Counter(), Counter(), Counter()
    ids = set(started) | set(completed)
    for key in ids:
        item = completed.get(key, started.get(key))
        tool = item.get("tool", "unknown")
        tools[tool] += 1
        command = item.get("arguments", {}).get("command")
        # Schema discovery is not execution of the described command.
        if isinstance(command, str) and not tool.startswith("describe_"):
            commands[command] += 1
        result = item.get("result") or {}
        if item.get("status") == "failed" or item.get("error") or result.get("isError"):
            failed[tool] += 1
    return {
        "mcp_attempts": len(ids),
        "completed_calls": len(completed),
        "unfinished_calls": len(set(started) - set(completed)),
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
        "metrics": stats,
        "comparison_eligible": False,
        "comparison_blockers": [
            "Historical sessions do not pin a common agent model/version and identical task, evaluator and environment across plugin versions."
        ],
    }


def audit(root, registry):
    entries = registry["runs"]
    if len({e["id"] for e in entries}) != len(entries):
        raise ValueError("Duplicate run ID")
    runs = [audit_run(root, e) for e in entries]
    return {
        "purpose": "Find cross-task workflow friction, not score modeling quality or claim improvement.",
        "families": sorted({r["family"] for r in runs if r["available"]}),
        "runs": runs,
        "promotion_authorized": False,
        "limitation": "Historical heterogeneous observations only. Missing data stays unknown; task success and efficiency are separate.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = audit(root, json.loads(args.registry.read_text()))
    args.output.write_text(json.dumps(report, indent=2) + "\n")
