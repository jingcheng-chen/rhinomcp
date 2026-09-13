import copy
import json

import pytest

from experiments.workflow.audit import audit
from experiments.workflow.flaws import trace, report_run, rank, sha


def event(id, tool, args=None, result=None, status="completed", kind="item.completed"):
    return {
        "type": kind,
        "item": {
            "id": id,
            "type": "mcp_tool_call",
            "tool": tool,
            "arguments": args or {},
            "result": result,
            "status": status,
        },
    }


def write_trace(tmp_path, events):
    path = tmp_path / "experiments/runs/run"
    (path / "modeler").mkdir(parents=True, exist_ok=True)
    (path / "modeler/events.jsonl").write_text("\n".join(map(json.dumps, events)))
    return path


def findings(tmp_path, events):
    path = write_trace(tmp_path, events)
    return report_run(path, {"id": "run"}, {}, {})["findings"]


@pytest.mark.parametrize(
    "result",
    [
        {"isError": True, "content": "problem"},
        {"is_error": True},
        {"structured_content": {"result": {"success": False, "message": "problem"}}},
        {"content": json.dumps({"result": {"success": False}})},
        {"content": [{"type": "text", "text": json.dumps({"success": False})}]},
    ],
)
def test_error_envelopes_across_providers(tmp_path, result):
    f = findings(tmp_path, [event("x", "create_object", result=result)])
    assert any(x["category"] == "failed_call" for x in f)


def test_negative_geometry_is_not_failed_command(tmp_path):
    f = findings(
        tmp_path,
        [
            event(
                "x",
                "analyze_objects",
                result={
                    "structured_content": {
                        "result": {"valid": False, "objects": [{"success": False}]}
                    }
                },
            )
        ],
    )
    assert not f


def test_pairing_concurrent_completion_order_and_unfinished(tmp_path):
    p = write_trace(
        tmp_path,
        [
            event("a", "get_objects", kind="item.started"),
            event("b", "get_object_info", kind="item.started"),
            event("b", "get_object_info"),
            event("a", "get_objects"),
            event("c", "create_object", kind="item.started"),
        ],
    )
    rows, usage, _ = trace(p / "modeler/events.jsonl")
    assert [r["id"] for r in rows] == ["a", "b", "c"]
    assert [r["completed"] for r in rows] == [True, True, False]
    assert usage is None


@pytest.mark.parametrize("write_status", ["completed", "failed", "in_progress"])
def test_reads_invalidate_even_after_failed_or_unfinished_write(tmp_path, write_status):
    events = [
        event("a", "get_objects", result={"objects": []}),
        event(
            "b",
            "create_object",
            status=write_status,
            kind="item.started" if write_status == "in_progress" else "item.completed",
        ),
        event("c", "get_objects", result={"objects": []}),
    ]
    assert not any(
        f["category"] == "redundant_read" for f in findings(tmp_path, events)
    )


def test_discovery_duplicates_are_static_and_distinct_from_new_topics(tmp_path):
    events = [
        event("a", "get_modeling_guidance", {"topic": "transforms"}, {"text": "guide"}),
        event("b", "create_object"),
        event(
            "c", "get_modeling_guidance", {"topic": "verification"}, {"text": "guide"}
        ),
        event("d", "get_modeling_guidance", {"topic": "transforms"}, {"text": "guide"}),
    ]
    fs = findings(tmp_path, events)
    duplicate = [f for f in fs if f["category"] == "redundant_read"]
    assert len(duplicate) == 1 and duplicate[0]["cost_call_ids"] == ["d"]
    assert duplicate[0]["call_ids"] == ["a", "d"]
    assert len([f for f in fs if f["category"] == "discovery"]) == 3


def test_different_result_or_query_is_not_redundant(tmp_path):
    events = [
        event("a", "get_objects", result={"objects": []}),
        event("b", "get_objects", result={"objects": ["new"]}),
        event("c", "get_objects", {"offset": 10}, result={"objects": ["new"]}),
    ]
    assert not findings(tmp_path, events)


def test_schema_queries_are_not_mutations_or_typed_fallbacks(tmp_path):
    f = findings(tmp_path, [event("a", "describe_command", {"command": "run_command"})])
    assert [x["category"] for x in f] == ["discovery"]


def test_retry_links_correct_target_and_wrapped_calls(tmp_path):
    events = [
        event(
            "a",
            "assembly_command",
            {"command": "modify_object", "params": {"id": "one"}},
            status="failed",
        ),
        event(
            "b",
            "assembly_command",
            {"command": "modify_object", "params": {"id": "two"}},
        ),
        event(
            "c",
            "assembly_command",
            {
                "command": "modify_object",
                "params": {"id": "one", "translation": [1, 0, 0]},
            },
        ),
    ]
    fs = [f for f in findings(tmp_path, events) if f["category"] == "retry_after_error"]
    assert len(fs) == 1 and fs[0]["call_ids"] == ["a", "c"]
    assert fs[0]["confidence"] == "candidate"


def test_normal_cleanup_not_recovery_but_named_recreation_is(tmp_path):
    events = [
        event("a", "create_object", {"name": "profile"}, {"id": "one"}),
        event("b", "extrude_curve", {"curve_id": "one"}),
        event("c", "delete_object", {"id": "one"}),
    ]
    assert not findings(tmp_path, events)
    events.append(event("d", "create_object", {"name": "profile"}, {"id": "two"}))
    assert [f["category"] for f in findings(tmp_path, events)] == ["recovery_loop"]


def test_script_requires_review_before_typed_alternative_claim(tmp_path):
    fs = findings(tmp_path, [event("a", "run_command", {"command": "_Box"})])
    assert fs[0]["confidence"] == "candidate"
    assert fs[0]["subtype"] == "requires_catalog_review"


def test_exact_unique_timing_matches_and_ambiguous_repeats(tmp_path):
    events = [
        event("a", "create_object", status="failed"),
        event("b", "get_objects"),
        event("c", "get_objects"),
    ]
    path = write_trace(tmp_path, events)
    timing = path / "calls.jsonl"
    timing.write_text(
        "\n".join(
            json.dumps({"tool": t, "arguments": {}, "elapsed_seconds": 0.5})
            for t in ["create_object", "get_objects", "get_objects"]
        )
    )
    rows, _, _ = trace(path / "modeler/events.jsonl", timing)
    assert [r["seconds"] for r in rows] == [0.5, None, None]
    report = report_run(path, {"id": "run"}, {}, {})
    assert report["timing"]["timed_calls"] == 1


def semantic_review(path, category="wrong_default"):
    return {
        "events_sha256": sha(path / "modeler/events.jsonl"),
        "findings": [
            {
                "category": category,
                "subtype": "review_case",
                "tool": "modify_object",
                "confidence": "reviewed",
                "call_ids": ["a"],
                "cost_call_ids": ["a"],
                "reason": "Reviewed evidence",
                "evidence": [
                    {
                        "path": "modeler/events.jsonl",
                        "sha256": sha(path / "modeler/events.jsonl"),
                        "quote": "modify_object",
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "category",
    [
        "wrong_default",
        "misleading_response",
        "typed_fallback",
        "orchestration",
        "unmet_capability",
    ],
)
def test_semantic_categories_require_hash_bound_evidence(tmp_path, category):
    path = write_trace(tmp_path, [event("a", "modify_object")])
    entry = {"id": "run", "review": semantic_review(path, category)}
    if category == "typed_fallback":
        catalog = path / "tool-definitions.json"
        catalog.write_text('[{"name":"modify_object"}]')
        entry["review"]["findings"][0].update(
            typed_alternative="modify_object",
            catalog={"path": catalog.name, "sha256": sha(catalog)},
        )
    report = report_run(path, entry, {}, {})
    assert report["findings"][0]["category"] == category
    (path / "modeler/events.jsonl").write_text("changed")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        report_run(path, entry, {}, {})


@pytest.mark.parametrize("problem", ["quote", "hash", "id", "escape", "category"])
def test_invalid_review_refused(tmp_path, problem):
    path = write_trace(tmp_path, [event("a", "modify_object")])
    review = semantic_review(path)
    finding = review["findings"][0]
    if problem == "quote":
        finding["evidence"][0]["quote"] = "absent quote"
    elif problem == "hash":
        finding["evidence"][0]["sha256"] = "wrong"
    elif problem == "id":
        finding["call_ids"] = ["unknown"]
    elif problem == "escape":
        finding["evidence"][0]["path"] = "../../outside"
    else:
        finding["category"] = "invented"
    with pytest.raises(ValueError):
        report_run(path, {"id": "run", "review": review}, {}, {})


def test_fidelity_does_not_rewrite_verdict_or_accuse_successful_tools(tmp_path):
    path = write_trace(
        tmp_path, [event("a", "create_object", result={"success": True})]
    )
    verdict = {"status": "fail", "checks": {"surface_to_reference": False}}
    (path / "evaluation.json").write_text(json.dumps(verdict))
    result = {"complete": True}
    normal = report_run(path, {"id": "run"}, verdict, result)
    assert [f["category"] for f in normal["findings"]] == ["completion_contradiction"]
    entry = {
        "id": "run",
        "review": {
            "events_sha256": sha(path / "modeler/events.jsonl"),
            "fidelity": {
                "evaluation_sha256": sha(path / "evaluation.json"),
                "reason": "Reviewed shape-only miss",
            },
        },
    }
    reviewed = report_run(path, entry, verdict, result)
    assert not reviewed["findings"] and reviewed["fidelity_note"]
    assert verdict["status"] == "fail"


def test_unmet_capability_statement_is_only_a_candidate(tmp_path):
    path = write_trace(tmp_path, [])
    f = report_run(
        path, {"id": "run"}, {}, {"summary": "There is no available tool for this."}
    )["findings"]
    assert f[0]["category"] == "unmet_capability" and f[0]["confidence"] == "candidate"


def test_ranking_frequency_times_cost_and_unknown_time(tmp_path):
    path = write_trace(tmp_path, [event("a", "create_object", status="failed")])
    run = {"id": "r", "family": "f", "flaws": report_run(path, {"id": "r"}, {}, {})}
    second = copy.deepcopy(run)
    second["id"] = "s"
    ranked = rank([run, second], "tool")[0]
    assert ranked["frequency"] == 2 and ranked["score_calls"] == 2
    assert ranked["mean_cost_calls"] == 1 and ranked["score_seconds"] is None
    assert ranked["measured_seconds_subtotal"] == 0
    assert ranked["tool"] == "create_object"


def test_duplicate_source_cannot_inflate_ranking(tmp_path):
    entries = [
        {"id": id, "family": "f", "run": "experiments/runs/same"} for id in ["a", "b"]
    ]
    with pytest.raises(ValueError, match="Duplicate run path"):
        audit(tmp_path, {"runs": entries})


def test_reviewed_fallback_cannot_invent_an_available_tool(tmp_path):
    path = write_trace(tmp_path, [event("a", "run_command")])
    review = semantic_review(path, "typed_fallback")
    review["findings"][0]["evidence"][0]["quote"] = "run_command"
    with pytest.raises(ValueError, match="catalog"):
        report_run(path, {"id": "r", "review": review}, {}, {})


def test_operation_map_counts_calls_without_assuming_an_optimum(tmp_path):
    path = write_trace(
        tmp_path, [event("a", "create_object"), event("b", "analyze_objects")]
    )
    review = {
        "events_sha256": sha(path / "modeler/events.jsonl"),
        "required_operations": [
            {"id": "construct", "call_ids": ["a"]},
            {"id": "verify", "call_ids": ["b"]},
        ],
    }
    report = report_run(path, {"id": "r", "review": review}, {}, {})
    assert [o["calls"] for o in report["required_operations"]] == [1, 1]
    review["required_operations"][0]["call_ids"] = ["unknown"]
    with pytest.raises(ValueError):
        report_run(path, {"id": "r", "review": review}, {}, {})


def test_label_validation_detects_disagreement_and_missing_evidence(tmp_path):
    from experiments.workflow.audit import validate_labels

    path = write_trace(tmp_path, [event("a", "get_objects")])
    report = audit(
        tmp_path,
        {"runs": [{"id": "r", "family": "f", "run": str(path.relative_to(tmp_path))}]},
    )
    labels = {"runs": [{"id": "r", "calls": 1, "counts": {}}]}
    assert validate_labels(report, labels)["status"] == "matched"
    labels["runs"][0]["calls"] = 2
    with pytest.raises(ValueError):
        validate_labels(report, labels)
    labels["runs"][0]["id"] = "absent"
    assert validate_labels(report, labels)["status"] == "incomplete"


def test_registered_trace_calibration_when_local_evidence_is_available():
    from experiments.workflow.audit import validate_labels
    from experiments.runner import ROOT

    registry = json.loads((ROOT / "experiments/workflow/flaw-runs.json").read_text())
    if not all(
        (ROOT / e["run"] / "modeler/events.jsonl").exists() for e in registry["runs"]
    ):
        pytest.skip(
            "Full traces are local evidence; synthetic controls remain portable"
        )
    report = audit(ROOT, registry)
    labels = json.loads((ROOT / "experiments/workflow/flaw-labels.json").read_text())
    assert len(validate_labels(report, labels)["checked"]) == 23
    latest = report["rankings"]["observed_flaws_by_cohort"]["released-0.4.0"]
    assert len(latest) == 1 and latest[0]["category"] == "redundant_read"
    assert latest[0]["frequency"] == 2


def test_missing_response_is_not_evidence_of_an_identical_read(tmp_path):
    assert not findings(
        tmp_path, [event("a", "get_objects"), event("b", "get_objects")]
    )


def test_missing_runtime_method_is_not_a_missing_object():
    from experiments.workflow.flaws import cause

    assert (
        cause(
            {
                "error": "Error executing tool update_object_attributes: Communication error with Rhino: Method not found: 'System.String Newtonsoft.Json.Linq.JToken.ToString(Newtonsoft.Json.Formatting)'."
            }
        )
        == "runtime_exception"
    )
    assert cause({"error": "Object with given id not found"}) == "missing_object"


def test_error_only_result_counts_failure_but_object_data_does_not(tmp_path):
    import json
    from experiments.workflow.flaws import trace

    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "id": str(i),
                        "type": "mcp_tool_call",
                        "tool": "get_object_info",
                        "status": "completed",
                        "arguments": {},
                        "result": {"structured_content": {"result": result}},
                    },
                }
            )
            for i, result in enumerate(
                [
                    {"error": "Object lookup requires id or name"},
                    {"id": "1", "error": "custom data"},
                ]
            )
        )
    )
    rows, _, _ = trace(path)
    assert [r["failed"] for r in rows] == [True, False]
