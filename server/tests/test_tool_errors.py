"""Tool failures must reach MCP clients with their original text.

MCP SDK 2.x reports an unexpected exception to the client as only
"Error executing tool <name>". RhinoMCPServer re-raises tool failures as
ToolError so the message survives, while direct calls of the tool functions
keep raising their own exception types.
"""

from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

import rhinomcp
from rhinomcp.tools.delete_object import delete_object

RHINO_DOWN = "Could not connect to Rhino at 127.0.0.1:1999. Run `mcpstart`."


@pytest.mark.asyncio
async def test_connection_failure_text_reaches_the_client():
    # boolean_union re-raises transport failures instead of returning a string.
    with patch(
        "rhinomcp.tools.boolean_operations.get_rhino_connection",
        side_effect=Exception(RHINO_DOWN),
    ):
        with pytest.raises(ToolError, match="mcpstart") as info:
            await rhinomcp.mcp.call_tool("boolean_union", {"object_ids": ["a", "b"]})
    # The SDK's UnexpectedToolError subclass is the masking path.
    assert type(info.value) is ToolError
    assert str(info.value) == f"Error executing tool boolean_union: {RHINO_DOWN}"


@pytest.mark.asyncio
async def test_parameter_errors_keep_their_text():
    with pytest.raises(ToolError, match="specify exactly one of id, name") as info:
        await rhinomcp.mcp.call_tool("delete_object", {"id": "a", "name": "b"})
    assert type(info.value) is ToolError


def test_direct_calls_keep_the_tools_own_exception_types():
    with pytest.raises(ValueError, match="exactly one"):
        delete_object(None, id="a", name="b")
