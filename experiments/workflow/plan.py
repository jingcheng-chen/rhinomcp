"""Run the workflow planner on audited evidence; proposals cannot dispatch builders."""

import argparse
import json
from pathlib import Path
import time
import uuid
from experiments.runner import ROOT, role_instructions, run_session, save, sha256
from experiments.workflow.proposals import validate


def response_schema():
    # The response-format subset omits uniqueItems; authoritative validation below
    # still enforces the complete proposal schema and semantic constraints.
    schema = json.loads(
        (ROOT / "experiments/workflow/proposal.schema.json").read_text()
    )

    def compatible(node):
        if isinstance(node, dict):
            return {
                k: compatible(v)
                for k, v in node.items()
                if k not in {"uniqueItems", "minItems", "minLength"}
            }
        if isinstance(node, list):
            return [compatible(v) for v in node]
        return node

    return compatible(schema)


def run(report):
    directory = (
        ROOT
        / "experiments/runs"
        / (time.strftime("workflow-plan-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    )
    directory.mkdir()
    print(directory, flush=True)
    folder = ROOT / "experiments/workflow"
    evidence = {
        "audit": json.loads(report.read_text()),
        "investigation_seed": json.loads(
            (folder / "surface-feedback.proposal.json").read_text()
        ),
    }
    save(directory / "evidence.json", evidence)
    sources = [
        "experiments/workflow/audit.py",
        "experiments/workflow/plan.py",
        "experiments/workflow/proposals.py",
        "experiments/workflow/proposal.schema.json",
        "experiments/harness/roles/workflow_planner.md",
        "experiments/runner.py",
    ]
    pins = {name: sha256(ROOT / name) for name in sources}
    save(directory / "inputs.json", pins)
    for name in sources:
        p = directory / "source" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    result = run_session(
        directory / "planner",
        role_instructions("workflow_planner")
        + "\nProduce one investigation proposal from this evidence. Do not claim measured improvement. The investigation seed is a supervisor-authored proposal, not an accepted decision.\n"
        + json.dumps(evidence),
        response_schema(),
        180,
    )
    try:
        validate(result, observed_families=evidence["audit"]["families"])
    except ValueError as error:
        save(
            directory / "summary.json",
            {
                "status": "rejected_proposal",
                "reason": str(error),
                "builder_dispatched": False,
            },
        )
        raise
    if pins != {name: sha256(ROOT / name) for name in sources}:
        raise RuntimeError("Planner sources changed")
    save(
        directory / "summary.json",
        {
            "proposal": result,
            "status": "proposed",
            "builder_dispatched": False,
            "promotion_authorized": False,
        },
    )
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    run(parser.parse_args().report)
