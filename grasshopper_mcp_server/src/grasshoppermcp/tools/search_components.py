"""Search for components in the Grasshopper library."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def search_components(
    ctx: Context,
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search for components in the Grasshopper library.
    Use this to find the correct component names and GUIDs before creating definitions.

    Parameters:
    - query: Search term to match against component name, nickname, or description
    - category: Filter by component category (e.g., "Params", "Curve", "Surface", "Maths")
    - limit: Maximum number of results to return (default: 50)

    Returns:
    - count: Number of components found
    - components: List with name, nickname, category, subcategory, description, and guid

    Example:
        # Find all slider-related components
        result = search_components(query="slider")
        for comp in result["components"]:
            print(f"{comp['name']} ({comp['guid']})")

        # Find components in the Params category
        result = search_components(category="Params")
    """
    try:
        gh = get_grasshopper_connection()
        params = {"limit": limit}
        if query:
            params["query"] = query
        if category:
            params["category"] = category

        return gh.send_command("search_components", params)
    except Exception as e:
        logger.error(f"Error searching components: {str(e)}")
        return {"success": False, "message": str(e)}
