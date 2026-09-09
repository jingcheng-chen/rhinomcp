"""Public assembly contracts; parent topology and numeric bounds are explicit."""

import json
import math

from jsonschema import Draft202012Validator
from experiments.runner import ROOT


def load(path):
    task = json.loads(path.read_text())
    schema = json.loads((ROOT / "experiments/assembly_tasks/schema.json").read_text())
    Draft202012Validator(schema).validate(task)
    layers = set(task["layers"])
    root = task["root"]
    if root not in layers or any(
        p != root
        and (not p.startswith(root + "::") or p.rsplit("::", 1)[0] not in layers)
        for p in layers
    ):
        raise ValueError(
            "All layers must belong to the root and include every ancestor"
        )
    if len({p["name"] for p in task["parts"]}) != len(task["parts"]):
        raise ValueError("Part names must be unique")
    for part in task["parts"]:
        if part["layer"] not in layers or not all(
            math.isfinite(a) and math.isfinite(b) and b > a
            for a, b in zip(part["min"], part["max"])
        ):
            raise ValueError(
                "Each part needs an existing layer and finite positive bounds"
            )
    return task


def instruction(task):
    return (
        "Build this assembly in millimeters using one visible, unlocked valid solid BOX for each specified part. min/max are exact world bounds. Create exactly the listed hierarchy and assign every named part to its full layer path. All assembly layers must be visible and unlocked; no extra geometry or new layers. Preserve existing empty document layers, which are outside the task. Repeated intermediate and leaf names are intentional: use full paths to disambiguate. Inspect object attributes. The supervisor saves and judges independently. Read command schemas before using tools; report honestly.\n"
        + json.dumps(task, sort_keys=True)
    )
