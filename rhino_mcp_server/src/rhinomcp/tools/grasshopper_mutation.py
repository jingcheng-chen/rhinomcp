"""Grasshopper batched graph mutation tools."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import mcp
from rhinomcp.tools._grasshopper_common import send_grasshopper_command


@mcp.tool()
def gh_mutate_graph(
    ctx: Context,
    operations: List[Dict[str, Any]],
    graph_id: Optional[str] = None,
    preview_policy: Optional[Dict[str, Any]] = None,
    groups: Optional[List[Dict[str, Any]]] = None,
    layout: Optional[Dict[str, Any]] = None,
    verify: Optional[Dict[str, Any]] = None,
    recompute: bool = True,
    rollback_on_error: bool = True,
) -> Dict[str, Any]:
    """Mutate an existing or new Grasshopper graph in one batched operation."""
    params: Dict[str, Any] = {
        "operations": operations,
        "recompute": recompute,
        "rollback_on_error": rollback_on_error,
    }
    if graph_id is not None:
        params["graph_id"] = graph_id
    if preview_policy is not None:
        params["preview_policy"] = preview_policy
    if groups is not None:
        params["groups"] = groups
    if layout is not None:
        params["layout"] = layout
    if verify is not None:
        params["verify"] = verify
    return send_grasshopper_command("gh_mutate_graph", params)
