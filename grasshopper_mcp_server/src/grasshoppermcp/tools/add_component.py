"""Add a component to the Grasshopper canvas."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional, List


@mcp.tool()
def add_component(
    ctx: Context,
    component_name: str,
    position: List[float] = [0, 0],
    nickname: Optional[str] = None,
    component_guid: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a component to the Grasshopper canvas.

    Parameters:
    - component_name: Name of the component (e.g., "Circle", "Point", "Number Slider")
    - position: [x, y] position on canvas (default: [0, 0])
    - nickname: Optional nickname for the component instance
    - component_guid: Optional GUID of the component (for exact matching)

    Returns:
    - instance_id: GUID of the created component instance
    - name: Full name of the component
    - nickname: Nickname of the component
    - category: Category of the component
    - position: [x, y] position on canvas

    Common component names:
    - Primitives: "Point", "Circle", "Line", "Rectangle", "Box", "Sphere"
    - Parameters: "Number Slider", "Panel", "Boolean Toggle"
    - Math: "Addition", "Multiplication", "Division"
    - Lists: "List Item", "Merge", "Flatten"
    - Curves: "Interpolate", "Polyline", "Nurbs Curve"
    - Surfaces: "Loft", "Extrude", "Revolution"

    Example:
        # Add a circle component at position (100, 50)
        result = add_component(component_name="Circle", position=[100, 50], nickname="MyCircle")
        print(f"Created component: {result['instance_id']}")
    """
    try:
        if not component_name:
            return {"success": False, "message": "component_name is required"}

        gh = get_grasshopper_connection()
        params = {
            "component_name": component_name,
            "position": position
        }
        if nickname:
            params["nickname"] = nickname
        if component_guid:
            params["component_guid"] = component_guid

        result = gh.send_command("add_component", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error adding component: {str(e)}")
        return {"success": False, "message": str(e)}
