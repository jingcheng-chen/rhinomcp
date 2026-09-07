import copy
import json
from pathlib import Path
import pytest
from experiments.workflow.audit import audit, summarize_events
from experiments.workflow.proposals import validate


def test_calls_count_once_and_preserve_missing_usage(tmp_path):
    items = []

    def event(kind, id, tool, status, **extra):
        return {
            "type": kind,
            "item": {
                "id": id,
                "type": "mcp_tool_call",
                "tool": tool,
                "status": status,
                **extra,
            },
        }

    items += [
        event(
            "item.started",
            "1",
            "describe_command",
            "in_progress",
            arguments={"command": "create_object"},
        ),
        event(
            "item.completed",
            "1",
            "describe_command",
            "completed",
            arguments={"command": "create_object"},
        ),
    ]
    items += [
        event(
            "item.started",
            "2",
            "assembly_command",
            "in_progress",
            arguments={"command": "delete_object"},
        ),
        event(
            "item.completed",
            "2",
            "assembly_command",
            "failed",
            arguments={"command": "delete_object"},
            error={"message": "error"},
        ),
    ]
    items += [event("item.started", "3", "assembly_command", "in_progress")]
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(map(json.dumps, items)))
    r = summarize_events(p)
    assert (r["mcp_attempts"], r["failed_calls"], r["unfinished_calls"]) == (3, 1, 1)
    assert r["schema_queries"] == 1 and r["commands"] == {"delete_object": 1}
    assert r["usage"] is None


def test_missing_run_is_not_a_failed_task(tmp_path):
    r = audit(
        tmp_path,
        {"runs": [{"id": "missing", "family": "x", "run": "experiments/runs/missing"}]},
    )
    assert r["runs"][0]["available"] is False
    assert "task_verdict" not in r["runs"][0]
    assert r["promotion_authorized"] is False


def test_agent_claim_cannot_override_failure(tmp_path):
    p = tmp_path / "experiments/runs/run/modeler"
    p.mkdir(parents=True)
    (p / "events.jsonl").write_text("")
    (p / "result.json").write_text('{"complete":true}')
    (p.parent / "evaluation.json").write_text('{"status":"fail"}')
    r = audit(
        tmp_path,
        {"runs": [{"id": "run", "family": "x", "run": "experiments/runs/run"}]},
    )["runs"][0]
    assert r["task_verdict"] == "fail" and r["agent_claim_complete"] is True
    assert r["comparison_eligible"] is False


def seed():
    return json.loads(
        (
            Path(__file__).parents[1] / "workflow/surface-feedback.proposal.json"
        ).read_text()
    )


@pytest.mark.parametrize(
    "fault", ["held_out_seen", "held_out_not_tested", "efficiency_only"]
)
def test_reject_weak_generalization_proposals(fault):
    p = copy.deepcopy(seed())
    if fault == "held_out_seen":
        p["held_out_families"] = ["surface-construction"]
    elif fault == "held_out_not_tested":
        p["held_out_families"] = ["unlisted"]
    else:
        p["metrics"] = ["mcp_calls"]
    with pytest.raises(ValueError):
        validate(p)


def test_capability_proposal_does_not_require_a_defect():
    p = seed()
    p["kind"] = "new_capability"
    assert validate(p)["status"] == "proposed"


def test_audit_exposed_family_cannot_be_claimed_held_out():
    p = seed()
    with pytest.raises(ValueError, match="discovery audit"):
        validate(p, observed_families=["curved-panels"])


def test_response_subset_keeps_authoritative_uniqueness_check():
    import jsonschema
    from experiments.workflow.plan import response_schema

    assert "uniqueItems" not in json.dumps(response_schema())
    p = seed()
    p["validation_families"].append(p["validation_families"][0])
    with pytest.raises(jsonschema.ValidationError):
        validate(p)
