from mcp.server.fastmcp import Context, Image
from typing import Optional
import base64
from rhinomcp.server import get_rhino_connection, mcp, logger


@mcp.tool()
def capture_viewport(
    ctx: Context,
    viewport: str = "active",
    width: int = 800,
    height: int = 600,
    show_grid: bool = True,
    show_axes: bool = True,
    show_cplane_axes: bool = False,
    zoom_to_fit: bool = False,
) -> Image:
    """
    Capture a screenshot of a Rhino viewport for visual analysis.

    This tool captures the current state of a Rhino viewport as an image,
    allowing Claude to visually understand and analyze the 3D model.

    Parameters:
    - viewport: Target viewport to capture. Options:
        - "active": The currently active viewport (default)
        - "perspective": The perspective viewport
        - "top": Top orthographic view (plan view)
        - "front": Front orthographic view
        - "right": Right orthographic view
        - "back": Back orthographic view
        - "left": Left orthographic view
        - "bottom": Bottom orthographic view
        - Or any custom viewport name defined in the document
    - width: Image width in pixels (default: 800, range: 100-4096)
    - height: Image height in pixels (default: 600, range: 100-4096)
    - show_grid: Show the viewport grid (default: True)
    - show_axes: Show world axes indicator (default: True)
    - show_cplane_axes: Show construction plane axes (default: False)
    - zoom_to_fit: Zoom viewport to fit all objects before capture (default: False)

    Returns:
    An Image object that Claude can analyze visually.

    Use Cases:
    - Verify geometry creation matches user intent
    - Analyze spatial relationships between objects
    - Check visual appearance and layout
    - Debug modeling issues by seeing the actual result
    - Capture multiple views for comprehensive understanding

    Example workflow:
    1. capture_viewport(viewport="perspective") - Get overall 3D view
    2. capture_viewport(viewport="top", zoom_to_fit=True) - Get plan view
    3. capture_viewport(viewport="front") - Get elevation view
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
        }

        result = rhino.send_command("capture_viewport", params)

        # Decode base64 image data
        image_data = base64.b64decode(result["image_data"])

        logger.info(
            f"Captured viewport '{result.get('viewport_name', viewport)}' "
            f"({result.get('width', width)}x{result.get('height', height)})"
        )

        # Return MCP Image object for Claude to analyze
        return Image(data=image_data, format="png")

    except Exception as e:
        logger.error(f"Error capturing viewport: {str(e)}")
        raise Exception(f"Error capturing viewport: {str(e)}")
