"""Supervisor-only transport/schema checks against an isolated candidate checkout."""

import asyncio
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def validate(root):
    root = Path(root)
    spec = importlib.util.spec_from_file_location(
        "sweep_candidate", root / "server/src/rhinomcp/tools/advanced_geometry.py"
    )
    module = importlib.util.module_from_spec(spec)
    exec(compile(Path(spec.origin).read_text(), spec.origin, "exec"), module.__dict__)
    connection = Mock()
    connection.send_command.return_value = {"result_ids": ["result"], "message": "ok"}
    module.get_rhino_connection = lambda: connection
    for options in (
        {},
        {"cap_planar_ends": False},
        {"cap_planar_ends": True, "closed": True},
    ):
        result = module.sweep1(None, "rail", ["profile"], **options)
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)
        assert result["success"] is True
        name, params = connection.send_command.call_args.args
        assert name == "sweep1" and params["cap_planar_ends"] is options.get(
            "cap_planar_ends", False
        )
        assert params["closed"] is options.get("closed", False)
    connection.send_command.side_effect = RuntimeError(
        "Sweep planar end capping failed"
    )
    result = module.sweep1(None, "rail", ["profile"], cap_planar_ends=True)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    assert result["success"] is False
    contract = json.loads((root / "contracts/commands/sweep1.json").read_text())
    definitions = json.loads((root / "contracts/common/definitions.json").read_text())
    contract["$id"] = "https://rhinomcp.invalid/commands/sweep1.json"
    registry = Registry().with_resource(
        "https://rhinomcp.invalid/common/definitions.json",
        Resource.from_contents(definitions),
    )
    validator = Draft202012Validator(contract, registry=registry)
    valid = {
        "rail_id": "00000000-0000-0000-0000-000000000001",
        "profile_ids": ["00000000-0000-0000-0000-000000000002"],
    }
    for value in (True, False):
        validator.validate({**valid, "cap_planar_ends": value})
    validator.validate(valid)
    for value in ("true", 1, None, [], {}):
        assert list(validator.iter_errors({**valid, "cap_planar_ends": value}))
    assert contract["properties"]["cap_planar_ends"]["default"] is False
    return {"transport_cases": 4, "schema_cases": 8, "passed": True}


if __name__ == "__main__":
    import sys

    print(json.dumps(validate(sys.argv[1])))
