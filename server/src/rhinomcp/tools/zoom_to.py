from typing import Any, Dict, List, Literal, Optional

from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import get_rhino_connection, mcp
from rhinomcp.tools._params import given


@mcp.tool(
    title="Zoom to",
    annotations=ToolAnnotations(
        title="Zoom to",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def zoom_to(
    ctx: Context,
    target: Literal["all", "selection", "object_ids", "layer"],
    viewport: Optional[str] = None,
    object_ids: Optional[List[str]] = None,
    layer: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Frame a viewport on objects. Changes what the user sees, never the
    document: no undo record is created, so undo still reverts the last
    geometry edit.

    Parameters:
    - target: "all" (every visible object), "selection" (the current
      selection), "object_ids" (needs object_ids) or "layer" (needs layer)
    - viewport: viewport name such as "Perspective" or "Top"; default active
    - object_ids: ids of the objects to frame, when target is "object_ids"
    - layer: layer name or full path, when target is "layer"

    Returns the viewport's state afterwards (viewport_name, projection,
    display_mode, camera_location, camera_target, camera_up, lens_length) plus the
    bounding_box {min, max} it framed and the object_count inside it.
    """
    params = given(target=target, viewport=viewport, object_ids=object_ids, layer=layer)
    return get_rhino_connection().send_command("zoom_to", params)
