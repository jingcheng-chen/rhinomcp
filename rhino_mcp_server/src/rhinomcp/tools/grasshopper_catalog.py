"""Grasshopper component catalog discovery tools."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import send_grasshopper_command


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_search_components(
    ctx: Context,
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search the installed Grasshopper component library."""
    params: Dict[str, Any] = {"limit": limit}
    if query:
        params["query"] = query
    if category:
        params["category"] = category
    return send_grasshopper_command("gh_search_components", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_batch_search_components(ctx: Context, queries: List[str]) -> Dict[str, Any]:
    """Resolve multiple Grasshopper component names in one call."""
    return send_grasshopper_command("gh_batch_search_components", {"queries": queries})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_list_component_categories(ctx: Context) -> Dict[str, Any]:
    """List installed Grasshopper component categories and subcategories."""
    return send_grasshopper_command("gh_list_component_categories", {})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_get_available_components(
    ctx: Context,
    category: Optional[str] = None,
    include_description: bool = False,
    limit: int = 500,
) -> Dict[str, Any]:
    """Get installed Grasshopper components, optionally filtered by category."""
    params: Dict[str, Any] = {
        "include_description": include_description,
        "limit": limit,
    }
    if category:
        params["category"] = category
    return send_grasshopper_command("gh_get_available_components", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gh_get_component_type_info(
    ctx: Context,
    name: Optional[str] = None,
    guid: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect a Grasshopper component type before creating an instance."""
    params: Dict[str, Any] = {}
    if name:
        params["name"] = name
    if guid:
        params["guid"] = guid
    return send_grasshopper_command("gh_get_component_type_info", params)
