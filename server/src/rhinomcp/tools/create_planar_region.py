from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, mcp


@mcp.tool()
def create_planar_region(
    ctx: Context,
    outer_curve_id: str,
    inner_curve_ids: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create one planar Brep face from closed coplanar boundary curves.

    The outer curve bounds the face and each distinct inner curve becomes one
    hole. Inner loops must be strictly inside the outer loop and mutually
    disjoint and nonnested. Input curves are preserved.

    Returns the created object id and face/loop counts. Exceptions propagate as
    MCP tool errors.
    """
    params: Dict[str, Any] = {
        "outer_curve_id": outer_curve_id,
        "inner_curve_ids": inner_curve_ids or [],
    }
    if name is not None:
        params["name"] = name

    result = get_rhino_connection().send_command("create_planar_region", params)
    return {
        "success": True,
        "id": result.get("id"),
        "face_count": result.get("face_count"),
        "loop_count": result.get("loop_count"),
        "outer_loop_count": result.get("outer_loop_count"),
        "inner_loop_count": result.get("inner_loop_count"),
        "message": result.get("message", "Created planar region"),
    }
