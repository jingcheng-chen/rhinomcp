"""Validate investigation proposals without granting builder permissions."""

import json
from pathlib import Path
import jsonschema


def validate(proposal, observed_families=()):
    schema = json.loads(Path(__file__).with_name("proposal.schema.json").read_text())
    jsonschema.validate(proposal, schema)
    discovery = set(proposal["discovery_families"])
    validation = set(proposal["validation_families"])
    held_out = set(proposal["held_out_families"])
    if discovery & held_out or not held_out <= validation:
        raise ValueError(
            "Held-out families must be in validation and absent from discovery"
        )
    if held_out & set(observed_families):
        raise ValueError("Held-out families must not appear in the discovery audit")
    if "task_success" not in proposal["metrics"]:
        raise ValueError("Efficiency cannot be evaluated without task success")
    return proposal
