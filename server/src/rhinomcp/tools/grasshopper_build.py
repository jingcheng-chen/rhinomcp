"""Grasshopper batch graph construction tools."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import JsonValue, send_grasshopper_command


@mcp.tool()
def gh_build_graph(
    ctx: Context,
    components: List[Dict[str, Any]],
    connections: Optional[List[Dict[str, Any]]] = None,
    values: Optional[List[Dict[str, JsonValue]]] = None,
    preview_updates: Optional[Dict[str, Any]] = None,
    preview_policy: Optional[Dict[str, Any]] = None,
    groups: Optional[List[Dict[str, Any]]] = None,
    layout: Optional[Dict[str, Any]] = None,
    graph_id: Optional[str] = None,
    recompute: bool = True,
    rollback_on_error: bool = True,
    open_canvas: bool = True,
) -> Dict[str, Any]:
    """Create and wire a Grasshopper graph in one batched canvas operation.

    Each component needs an alias plus component_name or component_guid. Use
    aliases in connections, values, groups, and preview_policy; the response
    returns aliases mapped to generated instance IDs.

    Number Slider components support value/min/max/decimals. Layout supports
    max_columns to wrap long dataflow chains into a compact readable canvas.

    Minimal shape:
    components=[
        {"alias": "a", "component_name": "Number Slider", "value": 3.5, "min": 0, "max": 10},
        {"alias": "add", "component_name": "Addition"},
    ],
    connections=[{"source": "a", "target": "add", "target_input_index": 0}],
    layout={"enabled": True, "max_columns": 6}
    """
    params: Dict[str, Any] = {
        "components": components,
        "recompute": recompute,
        "rollback_on_error": rollback_on_error,
        "open_canvas": open_canvas,
    }
    if graph_id is not None:
        params["graph_id"] = graph_id
    if connections is not None:
        params["connections"] = connections
    if values is not None:
        params["values"] = values
    if preview_updates is not None:
        params["preview_updates"] = preview_updates
    if preview_policy is not None:
        params["preview_policy"] = preview_policy
    if groups is not None:
        params["groups"] = groups
    if layout is not None:
        params["layout"] = layout
    return send_grasshopper_command("gh_build_graph", params)
