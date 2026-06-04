"""Grasshopper parameter value tools."""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import JsonValue, send_grasshopper_command


@mcp.tool()
def gh_set_parameter_value(
    ctx: Context,
    value: JsonValue,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    input_index: int = 0,
    input_name: Optional[str] = None,
    min: Optional[float] = None,
    max: Optional[float] = None,
    decimals: Optional[int] = None,
) -> Dict[str, Any]:
    """Set a slider, toggle, panel, value list, or regular input parameter value."""
    params: Dict[str, Any] = {"value": value, "input_index": input_index}
    if instance_id:
        params["instance_id"] = instance_id
    if nickname:
        params["nickname"] = nickname
    if input_name:
        params["input_name"] = input_name
    if min is not None:
        params["min"] = min
    if max is not None:
        params["max"] = max
    if decimals is not None:
        params["decimals"] = decimals
    return send_grasshopper_command("gh_set_parameter_value", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_get_parameter_value(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    output_index: int = 0,
    output_name: Optional[str] = None,
    max_items: int = 100,
) -> Dict[str, Any]:
    """Read structured data from a Grasshopper output parameter."""
    params: Dict[str, Any] = {"output_index": output_index, "max_items": max_items}
    if instance_id:
        params["instance_id"] = instance_id
    if nickname:
        params["nickname"] = nickname
    if output_name:
        params["output_name"] = output_name
    return send_grasshopper_command("gh_get_parameter_value", params)
