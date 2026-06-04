"""Grasshopper component lifecycle tools."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import JsonValue, send_grasshopper_command


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_list_components(
    ctx: Context,
    category: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """List components on the active Grasshopper canvas."""
    params: Dict[str, Any] = {"limit": limit}
    if category:
        params["category"] = category
    if name:
        params["name"] = name
    return send_grasshopper_command("gh_list_components", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_get_component_info(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
) -> Dict[str, Any]:
    """Get detailed metadata for one Grasshopper canvas object."""
    params: Dict[str, Any] = {}
    if instance_id:
        params["instance_id"] = instance_id
    if nickname:
        params["nickname"] = nickname
    return send_grasshopper_command("gh_get_component_info", params)


@mcp.tool()
def gh_add_component(
    ctx: Context,
    component_name: str,
    component_guid: Optional[str] = None,
    position: Optional[List[float]] = None,
    nickname: Optional[str] = None,
    value: Optional[JsonValue] = None,
    min: Optional[float] = None,
    max: Optional[float] = None,
    decimals: Optional[int] = None,
    content: Optional[str] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a Grasshopper component to the active canvas."""
    params: Dict[str, Any] = {"component_name": component_name}
    if component_guid:
        params["component_guid"] = component_guid
    if position is not None:
        params["position"] = position
    if nickname:
        params["nickname"] = nickname
    if value is not None:
        params["value"] = value
    if min is not None:
        params["min"] = min
    if max is not None:
        params["max"] = max
    if decimals is not None:
        params["decimals"] = decimals
    if content is not None:
        params["content"] = content
    if text is not None:
        params["text"] = text
    return send_grasshopper_command("gh_add_component", params)


@mcp.tool()
def gh_layout_components(
    ctx: Context,
    component_ids: Optional[List[str]] = None,
    include_groups: bool = False,
    x_spacing: float = 220,
    y_spacing: float = 90,
    start_position: Optional[List[float]] = None,
    recompute: bool = False,
) -> Dict[str, Any]:
    """Lay out Grasshopper canvas objects using wires as a left-to-right graph."""
    params: Dict[str, Any] = {
        "include_groups": include_groups,
        "x_spacing": x_spacing,
        "y_spacing": y_spacing,
        "recompute": recompute,
    }
    if component_ids:
        params["component_ids"] = component_ids
    if start_position is not None:
        params["start_position"] = start_position
    return send_grasshopper_command("gh_layout_components", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
def gh_delete_component(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete one Grasshopper canvas object."""
    params: Dict[str, Any] = {}
    if instance_id:
        params["instance_id"] = instance_id
    if nickname:
        params["nickname"] = nickname
    return send_grasshopper_command("gh_delete_component", params)


@mcp.tool()
def gh_update_component(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    new_nickname: Optional[str] = None,
    position: Optional[List[float]] = None,
    enabled: Optional[bool] = None,
    preview: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update basic Grasshopper object metadata, position, enabled state, or preview state."""
    params: Dict[str, Any] = {}
    if instance_id:
        params["instance_id"] = instance_id
    if nickname:
        params["nickname"] = nickname
    if new_nickname is not None:
        params["new_nickname"] = new_nickname
    if position is not None:
        params["position"] = position
    if enabled is not None:
        params["enabled"] = enabled
    if preview is not None:
        params["preview"] = preview
    return send_grasshopper_command("gh_update_component", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
def gh_clear_canvas(
    ctx: Context,
    include_groups: bool = True,
    recompute: bool = False,
) -> Dict[str, Any]:
    """Delete objects from the active Grasshopper canvas."""
    return send_grasshopper_command(
        "gh_clear_canvas",
        {"include_groups": include_groups, "recompute": recompute},
    )
