"""Get all available components from the running Grasshopper instance."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def get_available_components(
    ctx: Context,
    category: Optional[str] = None,
    include_description: bool = False,
    limit: int = 500
) -> Dict[str, Any]:
    """
    Get all available components from the running Grasshopper instance.
    This returns components actually installed, including third-party plugins.

    Use this to discover what components are available in the current environment.

    Parameters:
    - category: Filter by category (e.g., "Params", "Curve", "Surface")
    - include_description: Include component descriptions (increases response size)
    - limit: Maximum number of components to return (default: 500)

    Returns:
    - count: Number of components found
    - components: List with name, nickname, category, subcategory, guid
    - categories: List of unique categories found

    Example:
        # Get all curve-related components
        result = get_available_components(category="Curve")

        # Get everything (may be large)
        result = get_available_components(limit=1000)
    """
    try:
        gh = get_grasshopper_connection()
        params = {
            "limit": limit,
            "include_description": include_description
        }
        if category:
            params["category"] = category

        return gh.send_command("get_available_components", params)
    except Exception as e:
        logger.error(f"Error getting available components: {str(e)}")
        return {"success": False, "message": str(e)}
