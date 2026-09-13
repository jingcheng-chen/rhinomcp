"""Signed zeros must not make successful Rhino mutations unusable by MCP clients."""

import json
import math
from unittest.mock import MagicMock, patch

import pytest

import rhinomcp


@pytest.fixture
def connection():
    # Other tests reload the server to exercise environment configuration.
    from rhinomcp.server import RhinoConnection

    payload = {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "circle",
        "type": "CIRCLE",
        "geometry": {"points": [[-0.0, -3.0, 0.0]], "degree": "2"},
        "_delta": {"bounds": [[-0.0, -1e-300, 0]]},
        "_health": {"value": -0.0},
        "other": [False, None, "-0.0", -2.5],
    }
    conn = RhinoConnection(host="127.0.0.1", port=1999)
    conn.sock = MagicMock()
    conn._capabilities = {"version": "0.4.1", "commands": []}
    conn.receive_full_response = MagicMock(
        return_value=json.dumps({"status": "success", "result": payload}).encode()
    )
    return conn


@pytest.mark.parametrize("mode", ["off", "warn", "strict"])
def test_bridge_normalizes_before_validation(connection, mode):
    with (
        patch("rhinomcp.server.RHINO_VALIDATE", mode),
        patch("rhinomcp.validation.validate_response") as validate,
    ):
        result = connection._send_command_once("create_object", {})

    # Equality alone cannot detect this regression: -0.0 == 0.0 in Python.
    point = result["geometry"]["points"][0]
    assert math.copysign(1, point[0]) == 1
    assert math.copysign(1, point[2]) == 1
    assert point[1] == -3.0
    bounds = result["_delta"]["bounds"][0]
    assert math.copysign(1, bounds[0]) == 1
    assert bounds[1] == -1e-300
    assert type(bounds[2]) is int
    assert math.copysign(1, result["_health"]["value"]) == 1
    assert result["other"] == [False, None, "-0.0", -2.5]
    assert result["other"][0] is False
    if mode == "off":
        validate.assert_not_called()
    else:
        validated = validate.call_args.args[1]
        assert math.copysign(1, validated["geometry"]["points"][0][0]) == 1
        assert "_delta" not in validated
        assert "_health" not in validated
    connection.sock.sendall.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", ["create_object", "get_objects"])
async def test_sdk_output_has_positive_zero(connection, tool):
    arguments = (
        {"type": "CIRCLE", "params": {"center": [0, 0, 0], "radius": 5}}
        if tool == "create_object"
        else {}
    )
    with (
        patch("rhinomcp.server.RHINO_VALIDATE", "off"),
        patch(f"rhinomcp.tools.{tool}.get_rhino_connection", return_value=connection),
    ):
        output = await rhinomcp.mcp.call_tool(tool, arguments)

    wire = json.loads(output.model_dump_json(by_alias=True))
    assert not wire["isError"]
    result = wire["structuredContent"]["result"]
    if tool == "get_objects":
        result = json.loads(result)
    point = result["geometry"]["points"][0]
    assert math.copysign(1, point[0]) == 1
    assert point[1] == -3.0
    text_result = json.loads(wire["content"][0]["text"])
    assert math.copysign(1, text_result["geometry"]["points"][0][0]) == 1
    connection.sock.sendall.assert_called_once()
