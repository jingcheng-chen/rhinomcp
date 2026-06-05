"""Grasshopper live preview capture tools."""

import base64
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context, Image

from rhinomcp.server import logger, mcp
from rhinomcp.tools._grasshopper_common import send_grasshopper_command


@mcp.tool()
def gh_capture_preview(
    ctx: Context,
    viewport: str = "perspective",
    width: int = 800,
    height: int = 600,
    show_grid: bool = True,
    show_axes: bool = True,
    show_cplane_axes: bool = False,
    graph_id: Optional[str] = None,
    targets: Optional[List[str]] = None,
    include_hidden: bool = False,
    recompute: bool = True,
    open_canvas: bool = True,
    padding_factor: float = 1.15,
) -> Image:
    """Capture live Grasshopper preview in a Rhino viewport without baking.

    The plugin computes preview bounds from visible IGH_PreviewObject
    ClippingBox values, optionally filtered by graph_id or aliases/GUIDs in
    targets, zooms the Rhino viewport to those bounds, and returns a PNG image.
    """
    params: Dict[str, Any] = {
        "viewport": viewport,
        "width": max(100, min(width, 4096)),
        "height": max(100, min(height, 4096)),
        "show_grid": show_grid,
        "show_axes": show_axes,
        "show_cplane_axes": show_cplane_axes,
        "include_hidden": include_hidden,
        "recompute": recompute,
        "open_canvas": open_canvas,
        "padding_factor": padding_factor,
    }
    if graph_id is not None:
        params["graph_id"] = graph_id
    if targets is not None:
        params["targets"] = targets

    result = send_grasshopper_command("gh_capture_preview", params)
    image_data = base64.b64decode(result["image_data"])
    logger.info(
        "Captured Grasshopper preview '%s' (%sx%s, %s preview objects)",
        result.get("viewport_name", viewport),
        result.get("width", width),
        result.get("height", height),
        result.get("captured_preview_object_count", "?"),
    )
    return Image(data=image_data, format="png")
