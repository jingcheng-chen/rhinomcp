"""Grasshopper document and canvas inspection tools."""

from typing import Any, Dict

from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import send_grasshopper_command


@mcp.tool(
    title="Create Grasshopper document",
    annotations=ToolAnnotations(
        title="Create Grasshopper document",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def gh_create_document(
    ctx: Context,
    new_if_missing: bool = True,
    make_active: bool = True,
    open_canvas: bool = True,
) -> Dict[str, Any]:
    """Create or activate a Grasshopper document for subsequent canvas commands."""
    return send_grasshopper_command(
        "gh_create_document",
        {
            "new_if_missing": new_if_missing,
            "make_active": make_active,
            "open_canvas": open_canvas,
        },
    )


@mcp.tool(
    title="Get Grasshopper document info",
    annotations=ToolAnnotations(
        title="Get Grasshopper document info",
        read_only_hint=True,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def gh_get_document_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the active Grasshopper document."""
    return send_grasshopper_command("gh_get_document_info", {})


@mcp.tool(
    title="Get Grasshopper canvas state",
    annotations=ToolAnnotations(
        title="Get Grasshopper canvas state",
        read_only_hint=True,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def gh_get_canvas_state(
    ctx: Context,
    include_connections: bool = True,
    include_values: bool = False,
    max_items: int = 20,
) -> Dict[str, Any]:
    """Return a structured snapshot of the active Grasshopper canvas."""
    return send_grasshopper_command(
        "gh_get_canvas_state",
        {
            "include_connections": include_connections,
            "include_values": include_values,
            "max_items": max_items,
        },
    )
