"""List components on the Grasshopper canvas."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def list_components(
    ctx: Context,
    category: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    List all components on the active Grasshopper canvas.

    Parameters:
    - category: Filter by component category (e.g., "Params", "Curve", "Surface")
    - name: Filter by component name (partial match)
    - limit: Maximum number of components to return (default: 100)

    Returns:
    - count: Number of components returned
    - components: List of component info (instance_id, name, nickname, category, position, etc.)

    Example:
        # List all curve-related components
        result = list_components(category="Curve")
        for comp in result["components"]:
            print(f"{comp['name']} at {comp['position']}")
    """
    try:
        gh = get_grasshopper_connection()
        params = {"limit": limit}
        if category:
            params["category"] = category
        if name:
            params["name"] = name

        return gh.send_command("list_components", params)
    except Exception as e:
        logger.error(f"Error listing components: {str(e)}")
        return {"success": False, "message": str(e)}
