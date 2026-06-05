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
    fail_on_verification_error: bool = False,
    recompute: bool = True,
    rollback_on_error: bool = True,
    open_canvas: bool = True,
) -> Dict[str, Any]:
    """Batch edit, rewire, and verify an existing or new Grasshopper graph.

    Use this after gh_build_graph for follow-up edits: insert components,
    disconnect/reconnect wires, update values/preview/nicknames, delete objects,
    group/layout the changed graph, recompute, and verify outputs in one
    rollback-safe call. Selectors in source, target, layout targets, groups, and
    preview_policy can be request-local aliases, persisted aliases, Grasshopper
    instance GUIDs, or nicknames.

    Port selection supports indices or names/nicknames:
    source_output_name="R", target_input_name="L".

    Insert a component between two existing components by GUID:
    operations=[
        {
            "op": "disconnect",
            "source": "source-guid",
            "source_output_name": "G",
            "target": "target-guid",
            "target_input_name": "L",
        },
        {"op": "create", "alias": "flatten", "component_name": "Flatten Tree"},
        {"op": "connect", "source": "source-guid", "source_output_name": "G", "target": "flatten"},
        {"op": "connect", "source": "flatten", "target": "target-guid", "target_input_name": "L"},
        {"op": "recompute"},
    ]

    Use layout={"enabled": True, "targets": ["source-guid", "flatten", "target-guid"], "max_columns": 4}
    to keep the edited area readable.
    """
    params: Dict[str, Any] = {
        "operations": operations,
        "fail_on_verification_error": fail_on_verification_error,
        "recompute": recompute,
        "rollback_on_error": rollback_on_error,
        "open_canvas": open_canvas,
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
