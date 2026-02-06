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
    Search for a component by name. Only needed for UNCOMMON components!

    MOST COMPONENTS DON'T NEED SEARCH - use directly in create_definition:
    "Number Slider", "Panel", "Point", "Line", "Circle", "Rectangle",
    "Extrude", "Loft", "Move", "Rotate", "Scale", "Series", "Range",
    "Addition", "Multiplication", "Sine", "Cosine", "Tangent",
    "Unit X", "Unit Y", "Unit Z", "Construct Point", "Interpolate",
    "Cross Reference", "Graft", "Flatten", "Merge", etc.

    Only use search for unusual or third-party components.

    Parameters:
    - query: Search term (only for uncommon components)
    - category: Filter by category
    - limit: Max results (default: 50)

    Returns:
    - components: List with name, nickname, category, guid
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
