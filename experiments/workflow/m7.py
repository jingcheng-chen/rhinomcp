"""M7: split runs by grounding and capture-metadata use; compare flagged rates.

Read-only over recorded traces and the M1 audit. It adds no detector to the
flaw taxonomy: the two trace facts below are run attributes, the flagged-run
rule is the M1 report filtered by keep rule v2, and a supervisor review file may
override the metadata heuristic with quoted evidence. No Rhino access.
"""

import argparse
import json
from pathlib import Path

from experiments.workflow.audit import audit
from experiments.workflow.flaws import READS, canonical, sha, trace

# Keep rule v2: gateway-caused failures stay observations, not flaws.
GATEWAY_CAUSES = {"host_execution_refusal", "host_component_refusal", "gateway_scope"}

# Calls that change neither the document nor its geometry. Camera moves and
# selection changes are perception, not edits; discovery reads are static.
NON_EDITS = READS | {
    "get_context",
    "get_document_summary",
    "get_selected_objects_info",
    "measure_objects",
    "select_objects",
    "set_camera",
    "zoom_to",
    "get_rhinoscript_docs",
    "list_rhinoscript_modules",
    "search_rhinoscript_functions",
    "get_module_functions",
}

METADATA_KEYS = (
    "visible_object_count",
    "total_object_count",
    "scene_bounding_box",
    "camera_location",
    "camera_target",
    "camera_up",
    "lens_length",
    "display_mode",
    "viewport_name",
)


def capture_metadata(result):
    """The JSON text block capture_viewport returns beside its image, if any."""
    if not isinstance(result, dict):
        return None
    content = result.get("content")
    if not isinstance(content, list):
        return None
    for block in content:
        if block.get("type") != "text":
            continue
        try:
            value = json.loads(block.get("text", ""))
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and "visible_object_count" in value:
            return value
    return None


def _numbers(value, out):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(f"{value:g}")
        out.add(f"{value:.1f}")
        out.add(f"{round(value)}")
    elif isinstance(value, dict):
        for v in value.values():
            _numbers(v, out)
    elif isinstance(value, list):
        for v in value:
            _numbers(v, out)


def metadata_tokens(metadata):
    """Strings whose later appearance shows the metadata was used, not just received."""
    tokens = set(METADATA_KEYS)
    numbers = set()
    for key in (
        "scene_bounding_box",
        "camera_location",
        "camera_target",
        "lens_length",
    ):
        _numbers(metadata.get(key), numbers)
    # Bare small integers are too common to prove anything; keep decimals and
    # multi-digit values, and tie object counts to their words.
    tokens |= {n for n in numbers if "." in n or len(n.lstrip("-")) >= 2}
    for key in ("visible_object_count", "total_object_count"):
        count = metadata.get(key)
        if isinstance(count, int):
            tokens |= {f"{count} visible", f"{count} objects", f"{count} object"}
    return tokens


def trace_facts(path):
    """Grounding and capture facts from one run's Codex/Claude event trace."""
    rows, _, messages = trace(path / "modeler/events.jsonl", path / "calls.jsonl")
    ordered = sorted(rows, key=lambda r: r["line"])
    edits = [r for r in ordered if r["command"] not in NON_EDITS]
    first_edit_line = edits[0]["line"] if edits else None
    contexts = [
        r
        for r in ordered
        if r["command"] == "get_context" and r["completed"] and not r["failed"]
    ]
    grounded = bool(contexts) and (
        first_edit_line is None or contexts[0]["line"] < first_edit_line
    )
    captures = [
        r
        for r in ordered
        if r["command"] == "capture_viewport" and r["completed"] and not r["failed"]
    ]
    metadata_read = False
    evidence = None
    if captures:
        last = captures[-1]
        done = max(last["lines"])
        metadata = capture_metadata(last.get("result"))
        if metadata is not None:
            tokens = metadata_tokens(metadata)
            later_text = [m["text"] for m in messages if m["line"] > done]
            later_text += [
                canonical(r["arguments"]) for r in ordered if r["line"] > done
            ]
            for text in later_text:
                hit = next((t for t in tokens if t in text), None)
                if hit:
                    metadata_read = True
                    evidence = {"token": hit, "text": text[:300]}
                    break
    return {
        "calls": len(ordered),
        "edits": len(edits),
        "get_context_calls": len(contexts),
        "grounded": grounded,
        "capture_calls": len(captures),
        "captured": bool(captures),
        "metadata_present": bool(captures)
        and capture_metadata(captures[-1].get("result")) is not None,
        "metadata_read": metadata_read,
        "metadata_evidence": evidence,
        "camera_calls": sum(r["command"] in {"set_camera", "zoom_to"} for r in ordered),
        "events_sha256": sha(path / "modeler/events.jsonl"),
    }


def flagged(run):
    """Observed or reviewed findings, minus gateway-caused failed calls."""
    return [
        f
        for f in run.get("flaws", {}).get("findings", [])
        if f["confidence"] in {"observed", "reviewed"}
        and not (f["category"] == "failed_call" and f["subtype"] in GATEWAY_CAUSES)
    ]


def load_registries(paths):
    runs = []
    for path in paths:
        runs += json.loads(Path(path).read_text())["runs"]
    if len({r["id"] for r in runs}) != len(runs):
        raise ValueError("Duplicate run ID across registries")
    return {"runs": runs}


def apply_review(fact, run_id, review):
    """A reviewed judgment replaces the heuristic only with quoted trace evidence."""
    entry = (review or {}).get(run_id)
    if not entry:
        return fact
    if entry["events_sha256"] != fact["events_sha256"]:
        raise ValueError("Reviewed trace hash changed: " + run_id)
    if not entry.get("reason") or not entry.get("quote"):
        raise ValueError("Reviewed judgment needs a reason and a quote: " + run_id)
    return {
        **fact,
        "metadata_read": bool(entry["metadata_read"]),
        "metadata_evidence": {"reviewed": True, **entry},
    }


def describe(root, registries, review=None):
    report = audit(root, load_registries(registries))
    rows = []
    for run in report["runs"]:
        if not run["available"]:
            rows.append({"id": run["id"], "available": False})
            continue
        fact = apply_review(trace_facts(root / run["source"]), run["id"], review)
        fact["verified"] = fact["captured"] and fact["metadata_read"]
        flags = flagged(run)
        rows.append(
            {
                "id": run["id"],
                "available": True,
                "family": run["family"],
                "cohort": run["cohort"],
                "catalog": (run.get("environment") or {}).get("catalog_mode"),
                "task_verdict": run["task_verdict"],
                "session_status": run["session_status"],
                "agent_claim_complete": run["agent_claim_complete"],
                "failed_calls": run["metrics"]["failed_calls"],
                "flagged": bool(flags),
                "flags": sorted({f"{f['category']}/{f['subtype']}" for f in flags}),
                **fact,
            }
        )
    return report, rows


def group(rows, predicate):
    members = [r for r in rows if r.get("available") and predicate(r)]
    n = len(members)
    k = sum(r["flagged"] for r in members)
    return {
        "runs": n,
        "flagged": k,
        "rate": (k / n) if n else None,
        "run_ids": [r["id"] for r in members],
    }


GROUPS = (
    ("all runs", lambda r: True),
    ("grounded and verified", lambda r: r["grounded"] and r["verified"]),
    ("grounded only", lambda r: r["grounded"] and not r["verified"]),
    ("verified only", lambda r: not r["grounded"] and r["verified"]),
    ("neither", lambda r: not r["grounded"] and not r["verified"]),
    ("grounded (any)", lambda r: r["grounded"]),
    ("not grounded", lambda r: not r["grounded"]),
    ("verified (any)", lambda r: r["verified"]),
    ("not verified", lambda r: not r["verified"]),
    ("captured, metadata unused", lambda r: r["captured"] and not r["verified"]),
    ("full catalog", lambda r: r["catalog"] == "full"),
    ("native subset", lambda r: r["catalog"] == "native"),
)


def tables(current, baseline):
    groups = {}
    for name, predicate in GROUPS:
        groups[name] = {
            "0.5.0": group(current, predicate),
            "0.4.1": group(baseline, predicate),
        }
    families = sorted({r["family"] for r in current + baseline if r.get("available")})
    by_family = {
        family: {
            "0.5.0": group(current, lambda r, f=family: r["family"] == f),
            "0.4.1": group(baseline, lambda r, f=family: r["family"] == f),
        }
        for family in families
    }
    return groups, by_family


def percent(cell):
    if cell["runs"] == 0:
        return "no runs"
    return f"{cell['flagged']}/{cell['runs']} ({100 * cell['rate']:.0f}%)"


def markdown(groups, by_family):
    lines = [
        "| Group | Runs | Flagged runs | Flagged rate | 0.4.1 rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, cell in groups.items():
        c, b = cell["0.5.0"], cell["0.4.1"]
        rate = f"{100 * c['rate']:.0f}%" if c["runs"] else "n/a"
        lines.append(
            f"| {name} | {c['runs']} | {c['flagged']} | {rate} | {percent(b)} |"
        )
    lines += [
        "",
        "| Family | 0.5.0 runs | 0.5.0 flagged | 0.5.0 rate | 0.4.1 rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for family, cell in by_family.items():
        c, b = cell["0.5.0"], cell["0.4.1"]
        rate = f"{100 * c['rate']:.0f}%" if c["runs"] else "n/a"
        lines.append(
            f"| {family} | {c['runs']} | {c['flagged']} | {rate} | {percent(b)} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--current", type=Path, nargs="+", required=True)
    parser.add_argument("--baseline", type=Path, nargs="+", required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    review = json.loads(args.review.read_text()) if args.review else None
    current_report, current = describe(args.root, args.current, review)
    _, baseline = describe(args.root, args.baseline, review)
    groups, by_family = tables(current, baseline)
    result = {
        "rule": {
            "flagged": "At least one M1 finding with confidence observed or reviewed, excluding failed_call findings whose cause is gateway refusal, scope or budget (keep rule v2).",
            "grounded": "A completed get_context call precedes the first call to a tool outside the non-edit set, or the run makes no edit call.",
            "verified": "A completed capture_viewport call whose metadata text block is reflected in a later agent message or tool argument (key name, bounding-box or camera number, or object count with its noun), or a reviewed judgment with a quoted trace excerpt.",
            "non_edits": sorted(NON_EDITS),
        },
        "registries": {
            "current": [str(p) for p in args.current],
            "baseline": [str(p) for p in args.baseline],
            "review": str(args.review) if args.review else None,
        },
        "groups": groups,
        "by_family": by_family,
        "runs": {"0.5.0": current, "0.4.1": baseline},
        "markdown": markdown(groups, by_family),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if args.audit_output:
        args.audit_output.write_text(json.dumps(current_report, indent=2) + "\n")
    print(result["markdown"])


if __name__ == "__main__":
    main()
