from mcp.server.mcpserver import Context, Image
from mcp.types import TextContent, ToolAnnotations
import base64
import json
from typing import Dict, List, Literal, Optional
from rhinomcp.server import get_rhino_connection, mcp, logger

# What the text block after the image reports, in this order. The plugin
# computes every value; the tool only picks them out of its response.
METADATA_FIELDS = (
    "viewport_name",
    "display_mode",
    "projection",
    "width",
    "height",
    "camera_location",
    "camera_target",
    "camera_up",
    "lens_length",
    "scene_bounding_box",
    "visible_object_count",
    "total_object_count",
)


# Camera fitting and standard-view projection are temporary; the plugin restores
# the original viewport state after capture.
@mcp.tool(
    title="Capture viewport",
    annotations=ToolAnnotations(
        title="Capture viewport",
        read_only_hint=True,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def capture_viewport(
    ctx: Context,
    viewport: str = "active",
    width: int = 800,
    height: int = 600,
    show_grid: bool = True,
    show_axes: bool = True,
    show_cplane_axes: bool = False,
    zoom_to_fit: bool = False,
    format: Literal["png", "jpeg"] = "png",
    display_mode: Optional[str] = None,
    camera_location: Optional[List[float]] = None,
    camera_target: Optional[List[float]] = None,
    lens_length: Optional[float] = None,
    frame_object_ids: Optional[List[str]] = None,
    frame_bbox: Optional[Dict[str, List[float]]] = None,
) -> list[Image | TextContent]:
    """
    Capture a Rhino viewport as an image plus metadata saying what it shows.

    Parameters:
    - viewport: Target viewport to capture. Options:
        - "active": The currently active viewport (default)
        - "perspective": The perspective viewport
        - "top", "front", "right", "back", "left", "bottom": standard
          orthographic views
        - Or any custom viewport name defined in the document
    - width: Image width in pixels (default: 800, range: 100-4096)
    - height: Image height in pixels (default: 600, range: 100-4096)
    - show_grid: Show the viewport grid (default: True)
    - show_axes: Show world axes indicator (default: True)
    - show_cplane_axes: Show construction plane axes (default: False)
    - zoom_to_fit: Fit visible objects to the requested image dimensions (default: False)
    - format: "png" (default) or "jpeg" (smaller, lossy; saves context)
    - display_mode: Display mode name for this capture, e.g. "Shaded",
      "Wireframe", "Rendered", "Ghosted", "Technical", "Arctic". An unknown
      name is refused with the list of available modes.
    - camera_location / camera_target: [x, y, z] explicit camera for this
      capture; pass either or both. lens_length (mm) sets the 35mm-equivalent
      lens of a perspective view.
    - frame_object_ids: object ids to frame, or
      frame_bbox: {"min": [x, y, z], "max": [x, y, z]} world box to frame.
      An explicit camera (camera_location, camera_target or lens_length)
      cannot be combined with framing (frame_object_ids, frame_bbox or
      zoom_to_fit=True); the plugin refuses that with invalid_argument.

    Display mode, camera, lens and framing are temporary: the viewport is
    restored exactly as it was after the capture.

    Returns:
    The image, then a text block with a JSON object: viewport_name,
    display_mode, projection ("perspective" or "parallel"), width, height,
    camera_location, camera_target, camera_up, lens_length,
    scene_bounding_box ({min, max}, null for an empty document),
    visible_object_count and total_object_count. Read it to confirm the
    picture shows what you meant to look at.

    Example workflow:
    1. capture_viewport(viewport="perspective") - overall 3D view
    2. capture_viewport(viewport="top", zoom_to_fit=True) - plan view
    3. capture_viewport(frame_object_ids=[id], display_mode="Wireframe") - inspect one part
    4. capture_viewport(camera_location=[50, -80, 40], camera_target=[0, 0, 10]) - known angle
    """
    try:
        rhino = get_rhino_connection()

        params = {
            "viewport": viewport,
            "width": max(100, min(width, 4096)),
            "height": max(100, min(height, 4096)),
            "show_grid": show_grid,
            "show_axes": show_axes,
            "show_cplane_axes": show_cplane_axes,
            "zoom_to_fit": zoom_to_fit,
            "format": format,
        }
        optional = {
            "display_mode": display_mode,
            "camera_location": camera_location,
            "camera_target": camera_target,
            "lens_length": lens_length,
            "frame_object_ids": frame_object_ids,
            "frame_bbox": frame_bbox,
        }
        params.update({k: v for k, v in optional.items() if v is not None})

        result = rhino.send_command("capture_viewport", params)

        # Decode base64 image data
        image_data = base64.b64decode(result["image_data"])

        logger.info(
            f"Captured viewport '{result.get('viewport_name', viewport)}' "
            f"({result.get('width', width)}x{result.get('height', height)})"
        )

        metadata = {key: result.get(key) for key in METADATA_FIELDS}
        return [
            # The plugin's mime_type says what it actually encoded.
            Image(
                data=image_data,
                format=result.get("mime_type", "image/png").split("/")[-1],
            ),
            TextContent(type="text", text=json.dumps(metadata, indent=2)),
        ]

    except Exception as e:
        logger.error(f"Error capturing viewport: {str(e)}")
        raise
