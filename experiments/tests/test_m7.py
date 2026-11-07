import json

import pytest

from experiments.workflow import m7


def event(id, tool, args=None, result=None, kind="item.completed", line_result=None):
    return {
        "type": kind,
        "item": {
            "id": id,
            "type": "mcp_tool_call",
            "tool": tool,
            "arguments": args or {},
            "result": result,
            "status": "completed" if kind == "item.completed" else "in_progress",
        },
    }


def message(id, text):
    return {
        "type": "item.completed",
        "item": {"id": id, "type": "agent_message", "text": text},
    }


def capture_result(visible=3, total=3):
    metadata = {
        "viewport_name": "Perspective",
        "display_mode": "Shaded",
        "projection": "perspective",
        "width": 800,
        "height": 600,
        "camera_location": [120.5, -90.25, 60.0],
        "camera_target": [50.0, 25.0, 10.0],
        "camera_up": [0, 0, 1],
        "lens_length": 50.0,
        "scene_bounding_box": {"min": [0.0, 0.0, 0.0], "max": [100.0, 50.0, 30.0]},
        "visible_object_count": visible,
        "total_object_count": total,
    }
    return {
        "content": [
            {"type": "image", "data": "AAAA", "mimeType": "image/png"},
            {"type": "text", "text": json.dumps(metadata)},
        ]
    }


def write(tmp_path, events):
    path = tmp_path / "experiments/runs/run"
    (path / "modeler").mkdir(parents=True)
    (path / "modeler/events.jsonl").write_text("\n".join(map(json.dumps, events)))
    return path


def test_grounded_requires_context_before_first_edit(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "get_document_summary"),
                event("b", "get_context", result={"content": []}),
                event("c", "create_object", {"type": "BOX"}),
            ],
        )
    )
    assert facts["grounded"] and facts["edits"] == 1


def test_context_after_edit_is_not_grounding(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "create_object", {"type": "BOX"}),
                event("b", "get_context", result={"content": []}),
            ],
        )
    )
    assert not facts["grounded"]


def test_inspection_without_edits_counts_context_anywhere(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "analyze_objects", {"ids": ["x"]}),
                event("b", "get_context", result={"content": []}),
            ],
        )
    )
    assert facts["grounded"] and facts["edits"] == 0


def test_capture_without_later_use_is_not_verified(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "create_object", {"type": "BOX"}),
                event("b", "capture_viewport", {}, capture_result()),
                message("m", json.dumps({"summary": "Done.", "complete": True})),
            ],
        )
    )
    assert facts["captured"] and facts["metadata_present"]
    assert not facts["metadata_read"]


def test_capture_metadata_used_in_summary_is_verified(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "create_object", {"type": "BOX"}),
                event("b", "capture_viewport", {}, capture_result()),
                message(
                    "m",
                    json.dumps(
                        {
                            "summary": "Capture shows 3 visible objects within bounds to (100, 50, 30).",
                            "complete": True,
                        }
                    ),
                ),
            ],
        )
    )
    assert facts["metadata_read"]
    assert facts["metadata_evidence"]["token"] in {"3 visible", "100", "50", "30"}


def test_numbers_match_whole_tokens_only():
    assert m7.mentions("10", "bounds (0, 10, 5)")
    assert not m7.mentions("10", "bounds to (100, 50, 30)")
    assert not m7.mentions("10", "at 10.5 mm")
    assert m7.mentions("scene_bounding_box", "the scene_bounding_box matches")


def test_capture_metadata_used_in_later_tool_argument(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("a", "create_object", {"type": "BOX"}),
                event("b", "capture_viewport", {}, capture_result()),
                event("c", "set_camera", {"camera_location": [120.5, -90.25, 60.0]}),
                message("m", json.dumps({"summary": "Done.", "complete": True})),
            ],
        )
    )
    assert facts["metadata_read"]


def test_small_integers_alone_do_not_prove_use(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event("b", "capture_viewport", {}, capture_result(visible=3, total=3)),
                message(
                    "m", json.dumps({"summary": "Built 3 legs.", "complete": True})
                ),
            ],
        )
    )
    assert not facts["metadata_read"]


def test_failed_capture_does_not_count(tmp_path):
    facts = m7.trace_facts(
        write(
            tmp_path,
            [
                event(
                    "b",
                    "capture_viewport",
                    {},
                    {"isError": True, "content": [{"type": "text", "text": "boom"}]},
                ),
            ],
        )
    )
    assert not facts["captured"]


def test_review_overrides_heuristic_only_with_matching_hash(tmp_path):
    path = write(
        tmp_path,
        [
            event("b", "capture_viewport", {}, capture_result()),
            message("m", json.dumps({"summary": "Done.", "complete": True})),
        ],
    )
    facts = m7.trace_facts(path)
    review = {
        "run": {
            "events_sha256": facts["events_sha256"],
            "metadata_read": True,
            "reason": "Agent compared the count in its text.",
            "quote": "Done.",
        }
    }
    assert m7.apply_review(facts, "run", review)["metadata_read"]
    with pytest.raises(ValueError):
        m7.apply_review(facts, "run", {"run": {**review["run"], "events_sha256": "0"}})
    with pytest.raises(ValueError):
        m7.apply_review(facts, "run", {"run": {**review["run"], "quote": ""}})


def test_flagged_excludes_gateway_refusals_only():
    def run(*findings):
        return {"flaws": {"findings": list(findings)}}

    gateway = {
        "category": "failed_call",
        "subtype": "host_execution_refusal",
        "confidence": "observed",
    }
    missing = {
        "category": "failed_call",
        "subtype": "missing_layer",
        "confidence": "observed",
    }
    candidate = {
        "category": "retry_after_error",
        "subtype": "x",
        "confidence": "candidate",
    }
    assert not m7.flagged(run(gateway, candidate))
    assert m7.flagged(run(gateway, missing)) == [missing]


def test_group_rates_and_markdown():
    rows = [
        {
            "available": True,
            "flagged": True,
            "grounded": True,
            "verified": True,
            "captured": True,
            "catalog": "full",
            "family": "a",
            "id": "1",
        },
        {
            "available": True,
            "flagged": False,
            "grounded": False,
            "verified": False,
            "captured": False,
            "catalog": "full",
            "family": "a",
            "id": "2",
        },
    ]
    groups, by_family = m7.tables(rows, [])
    assert groups["all runs"]["0.5.0"] == {
        "runs": 2,
        "flagged": 1,
        "rate": 0.5,
        "run_ids": ["1", "2"],
    }
    assert groups["neither"]["0.4.1"]["runs"] == 0
    text = m7.markdown(groups, by_family)
    assert "| all runs | 2 | 1 | 50% | no runs |" in text
