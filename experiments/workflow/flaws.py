"""Conservative trace classification; no Rhino access or inferred geometry verdicts."""

from collections import Counter, defaultdict
import hashlib
import json
import math
import re

TAXONOMY = (
    "failed_call",
    "retry_after_error",
    "discovery",
    "redundant_read",
    "orchestration",
    "typed_fallback",
    "misleading_response",
    "wrong_default",
    "recovery_loop",
    "unmet_capability",
    "completion_contradiction",
)
DISCOVERY = {
    "describe_command",
    "describe_modeling_command",
    "describe_capabilities",
    "get_commands",
    "get_modeling_guidance",
}
READS = DISCOVERY | {
    "get_objects",
    "get_object_info",
    "get_object_attributes",
    "analyze_objects",
    "get_layers",
    "get_document_info",
    "get_reference_image",
    "inspect_view",
    "capture_viewport",
}
WRAPPERS = {"assembly_command", "modeling_command"}
FALLBACKS = {
    "run_command",
    "execute_rhinoscript_python_code",
    "execute_rhinocommon_csharp_code",
    "execute_python_code",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload(result):
    """Decode only MCP/JSON result envelopes, never search arbitrary geometry."""
    for _ in range(8):
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (ValueError, TypeError):
                return result
        elif isinstance(result, dict):
            if result.get("isError") or result.get("is_error"):
                return result
            structured = result.get(
                "structured_content", result.get("structuredContent")
            )
            if structured is not None:
                result = structured
            elif set(result) == {"result"}:
                result = result["result"]
            elif "content" in result:
                content = result["content"]
                if isinstance(content, list):
                    content = "\n".join(
                        c.get("text", "") for c in content if c.get("type") == "text"
                    )
                result = content
            else:
                return result
        else:
            return result
    return result


def finite_seconds(value):
    return (
        value
        if type(value) in (int, float) and math.isfinite(value) and value >= 0
        else None
    )


def trace(path, timings=None):
    """Pair starts/completions in start order, preserving unfinished calls and lines."""
    calls, usage, messages = {}, None, []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        event = json.loads(line)  # Corrupt traces must not silently produce a ranking.
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
        item = event.get("item", {})
        if (
            item.get("type") == "agent_message"
            and event.get("type") == "item.completed"
        ):
            messages.append({"line": line_number, "text": item.get("text", "")})
        if item.get("type") != "mcp_tool_call" or event.get("type") not in {
            "item.started",
            "item.completed",
        }:
            continue
        key = item["id"]
        row = calls.setdefault(
            key, {"id": key, "line": line_number, "lines": [], "completed": False}
        )
        row["lines"].append(line_number)
        row.update({k: v for k, v in item.items() if k != "type"})
        if event["type"] == "item.completed":
            row["completed"] = True
    rows = list(calls.values())
    for row in rows:
        row["arguments"] = row.get("arguments") or {}
        row["tool"] = row.get("tool", "unknown")
        row["command"] = (
            row["arguments"].get("command", row["tool"])
            if row["tool"] in WRAPPERS
            else row["tool"]
        )
        row["params"] = (
            row["arguments"].get("params", {})
            if row["tool"] in WRAPPERS
            else row["arguments"]
        )
        row["payload"] = payload(row.get("result"))
        raw = row.get("result") or {}
        value = row["payload"]
        row["failed"] = bool(
            row.get("status") == "failed"
            or row.get("error")
            or (isinstance(raw, dict) and (raw.get("isError") or raw.get("is_error")))
            or (
                isinstance(value, dict)
                and (
                    value.get("success") is False
                    or value.get("isError")
                    or value.get("is_error")
                    or (set(value) == {"error"} and bool(value["error"]))
                )
            )
        )
        row["seconds"] = None
    # Timing logs have no event IDs. Match unique exact tool/arguments only;
    # ambiguous repeated signatures and gateway-rejected calls remain unknown.
    grouped, logged = defaultdict(list), defaultdict(list)
    for row in rows:
        grouped[(row["tool"], canonical(row["arguments"]))].append(row)
    if timings and timings.exists():
        for line in timings.read_text().splitlines():
            entry = json.loads(line)
            if "tool" in entry and "arguments" in entry:
                logged[(entry["tool"], canonical(entry["arguments"]))].append(entry)
        for signature, group in grouped.items():
            matches = logged[signature]
            if len(group) == len(matches) == 1:
                group[0]["seconds"] = finite_seconds(matches[0].get("elapsed_seconds"))
    return rows, usage, messages


def cause(row):
    text = canonical(row.get("error") or row.get("result") or "").lower()
    patterns = [
        (
            "gateway_scope",
            r"outside .*scope|not (?:allowed|exposed)|(?:call|tool) budget|document changed",
        ),
        (
            "schema_input",
            r"validation error|unexpected token|error reading|must exceed|missing|required|invalid (?:argument|parameter)|unknown (?:argument|parameter)",
        ),
        (
            "runtime_exception",
            r"object reference|exception|nullreference|method not found",
        ),
        ("transport", r"connection refused|timed? out|timeout|disconnected|socket"),
        ("missing_object", r"object.*not found|could not find.*object"),
        ("missing_layer", r"layer.*not found"),
    ]
    return next(
        (name for name, pattern in patterns if re.search(pattern, text)), "unknown"
    )


def classify(rows):
    findings = []
    by_id = {r["id"]: r for r in rows}

    def add(category, subtype, row, evidence=None, confidence="observed", reason=""):
        findings.append(
            {
                "category": category,
                "subtype": subtype,
                "tool": row["command"],
                "confidence": confidence,
                "call_ids": evidence or [row["id"]],
                "cost_call_ids": [row["id"]],
                "reason": reason,
            }
        )

    prior_error, reads, recent_mutations = {}, {}, []
    epoch = 0
    for row in rows:
        command, params = row["command"], row["params"]
        readonly = command in READS
        if row["failed"]:
            add(
                "failed_call",
                cause(row),
                row,
                reason="Explicit failed status, MCP error, or unsuccessful result envelope.",
            )
        # Discovery command names are targets, not executed modeling operations.
        retry_key = (
            command,
            params.get("command") if command in DISCOVERY else params.get("type"),
            params.get("id") or params.get("name"),
        )
        if retry_key in prior_error:
            previous = prior_error.pop(retry_key)
            add(
                "retry_after_error",
                "same_intent_candidate",
                row,
                [previous, row["id"]],
                "candidate",
                "Same command, target/type after a failure; parameter correction is allowed.",
            )
        if row["failed"]:
            prior_error[retry_key] = row["id"]
        if command in DISCOVERY:
            add(
                "discovery",
                "guidance"
                if command == "get_modeling_guidance"
                else "schema_or_catalog",
                row,
                confidence="observation",
                reason="Discovery cost, not automatically a product defect.",
            )
        if (
            readonly
            and row["completed"]
            and not row["failed"]
            and row["payload"] is not None
        ):
            signature = (
                command,
                canonical(params),
                0 if command in DISCOVERY else epoch,
            )
            previous = reads.get(signature)
            if previous and by_id[previous]["payload"] == row["payload"]:
                add(
                    "redundant_read",
                    "identical_response",
                    row,
                    [previous, row["id"]],
                    reason="Same query and response; no intervening possible document mutation (discovery is static).",
                )
            reads[signature] = row["id"]
        if command in FALLBACKS:
            add(
                "typed_fallback",
                "requires_catalog_review",
                row,
                confidence="candidate",
                reason="Script/macro use observed. Typed alternative and its availability require reviewed evidence.",
            )
        if not readonly:
            # Even failed/unfinished writes may have partially changed the document.
            epoch += 1
            if command in {"undo", "redo"} or (
                command == "run_command" and re.search(r"\b_?undo\b", str(params), re.I)
            ):
                add(
                    "recovery_loop",
                    "undo",
                    row,
                    confidence="candidate",
                    reason="Undo may be a required task operation; review intent.",
                )
            if command == "create_object" and params.get("name") and not row["failed"]:
                for previous in reversed(recent_mutations[-8:]):
                    if (
                        previous["command"] == "create_object"
                        and previous["params"].get("name") == params["name"]
                    ):
                        obj = previous["payload"]
                        oid = obj.get("id") if isinstance(obj, dict) else None
                        deletes = [
                            r
                            for r in recent_mutations[
                                recent_mutations.index(previous) + 1 :
                            ]
                            if r["command"] == "delete_object"
                            and (
                                (oid and r["params"].get("id") == oid)
                                or r["params"].get("name") == params["name"]
                            )
                        ]
                        if deletes:
                            add(
                                "recovery_loop",
                                "delete_recreate",
                                row,
                                [previous["id"], deletes[-1]["id"], row["id"]],
                                "candidate",
                                "Named object created, deleted and recreated; normal profile cleanup alone does not match.",
                            )
                        break
            recent_mutations.append(row)
    return findings


def reviewed(path, entry, rows):
    """Semantic judgments are explicit, hash-bound supervisor annotations."""
    review = entry.get("review")
    if not review:
        return [], None, None
    events = path / "modeler/events.jsonl"
    if review["events_sha256"] != sha(events):
        raise ValueError("Reviewed trace hash changed")
    ids = {r["id"] for r in rows}
    findings = []
    for finding in review.get("findings", []):
        if finding["category"] not in TAXONOMY or finding["confidence"] != "reviewed":
            raise ValueError("Invalid reviewed classification")
        for field in ("call_ids", "cost_call_ids"):
            if not set(finding[field]) <= ids:
                raise ValueError("Reviewed call ID absent")
        if not set(finding["cost_call_ids"]) <= set(finding["call_ids"]):
            raise ValueError("Cost calls must be evidence calls")
        if not finding.get("reason") or not finding.get("evidence"):
            raise ValueError("Semantic finding needs cited evidence")
        for evidence in finding["evidence"]:
            source = (path / evidence["path"]).resolve()
            source.relative_to(path.resolve())
            if (
                sha(source) != evidence["sha256"]
                or evidence["quote"] not in source.read_text()
            ):
                raise ValueError("Semantic evidence changed or quote absent")
        if finding["category"] == "typed_fallback":
            catalog = finding.get("catalog", {})
            source = (path / catalog.get("path", "")).resolve()
            source.relative_to(path.resolve())
            if not source.is_file() or sha(source) != catalog.get("sha256"):
                raise ValueError("Typed fallback requires a pinned exposed catalog")
            definitions = json.loads(source.read_text())
            if finding.get("typed_alternative") not in {d["name"] for d in definitions}:
                raise ValueError("Typed alternative was not exposed to this agent")
        findings.append(dict(finding))
    operations = review.get("required_operations")
    if operations is not None:
        if len({o["id"] for o in operations}) != len(operations):
            raise ValueError("Duplicate operation ID")
        for op in operations:
            if not set(op["call_ids"]) <= ids or len(op["call_ids"]) != len(
                set(op["call_ids"])
            ):
                raise ValueError("Invalid operation call IDs")
        operations = [{**op, "calls": len(op["call_ids"])} for op in operations]
    fidelity = review.get("fidelity")
    if fidelity:
        source = path / "evaluation.json"
        if sha(source) != fidelity["evaluation_sha256"] or not fidelity.get("reason"):
            raise ValueError("Fidelity review is not pinned to the verdict")
    return findings, operations, fidelity


def report_run(path, entry, evaluation, result):
    rows, _, messages = trace(path / "modeler/events.jsonl", path / "calls.jsonl")
    findings = classify(rows)
    semantic, operations, fidelity = reviewed(path, entry, rows)
    findings += semantic
    # Agent claims are not tool response claims. Never label every successful
    # creation/inspection misleading merely because final geometry failed.
    if (
        evaluation.get("status") == "fail"
        and result.get("complete") is True
        and not fidelity
    ):
        findings.append(
            {
                "category": "completion_contradiction",
                "subtype": "saved_file_rejects_claim",
                "tool": "agent_completion",
                "confidence": "observed",
                "call_ids": [],
                "cost_call_ids": [],
                "reason": "Agent claimed completion but independent saved-file verdict failed.",
            }
        )
    if result.get("summary") and not any(
        m["text"] == result["summary"] for m in messages
    ):
        messages.append({"line": None, "text": result["summary"]})
    for message in messages:
        if re.search(
            r"\b(?:missing|unavailable) (?:tool|capability)|\bno (?:available )?tool\b",
            message["text"],
            re.I,
        ):
            findings.append(
                {
                    "category": "unmet_capability",
                    "subtype": "agent_statement",
                    "tool": "agent_statement",
                    "confidence": "candidate",
                    "call_ids": [],
                    "cost_call_ids": [],
                    "reason": "Agent statement is a lead, not proof that the catalog lacks a capability.",
                    "message_line": message["line"],
                }
            )
    by_id = {r["id"]: r for r in rows}
    for number, finding in enumerate(findings, 1):
        costs = [by_id[i]["seconds"] for i in sorted(set(finding["cost_call_ids"]))]
        finding.update(
            id=f"{entry['id']}:{number}",
            evidence_lines=sorted(
                {line for i in finding["call_ids"] for line in by_id[i]["lines"]}
            ),
            cost_calls=len(set(finding["cost_call_ids"])),
            cost_seconds=sum(costs)
            if all(c is not None for c in costs) and costs
            else None,
            measured_seconds_subtotal=sum(c for c in costs if c is not None),
            timed_calls=sum(c is not None for c in costs),
        )
    return {
        "taxonomy_version": 1,
        "findings": findings,
        "counts": dict(sorted(Counter(f["category"] for f in findings).items())),
        "required_operations": operations,
        "fidelity_note": fidelity,
        "timing": {
            "source": "unique exact matches in calls.jsonl; gateway execution including guard overhead",
            "timed_calls": sum(r["seconds"] is not None for r in rows),
            "total_calls": len(rows),
        },
        "call_index": [
            {
                "id": r["id"],
                "tool": r["tool"],
                "command": r["command"],
                "lines": r["lines"],
                "failed": r["failed"],
                "completed": r["completed"],
                "seconds": r["seconds"],
            }
            for r in rows
        ],
    }


def rank(runs, dimension=None):
    groups = defaultdict(list)
    for run in runs:
        for finding in run.get("flaws", {}).get("findings", []):
            key = (finding["category"], finding["subtype"], finding["confidence"])
            if dimension:
                key += (run["family"] if dimension == "family" else finding["tool"],)
            groups[key].append((run, finding))
    result = []
    for key, values in groups.items():
        findings = [f for _, f in values]
        n = len(findings)
        total = sum(f["cost_calls"] for f in findings)
        seconds = [f["cost_seconds"] for f in findings]
        known = all(s is not None for s in seconds)
        row = {
            "category": key[0],
            "subtype": key[1],
            "confidence": key[2],
            "frequency": n,
            "runs": len({r["id"] for r, _ in values}),
            "mean_cost_calls": total / n,
            "score_calls": total,
            "score_seconds": sum(seconds) if known else None,
            "mean_cost_seconds": sum(seconds) / n if known else None,
            "measured_seconds_subtotal": sum(
                f["measured_seconds_subtotal"] for f in findings
            ),
            "timed_calls": sum(f["timed_calls"] for f in findings),
            "evidence": [{"run": r["id"], "finding": f["id"]} for r, f in values],
        }
        if dimension:
            row[dimension] = key[3]
        result.append(row)
    return sorted(
        result,
        key=lambda r: (
            -r["score_calls"],
            -r["frequency"],
            r["category"],
            r["subtype"],
            r.get(dimension or "", ""),
        ),
    )
