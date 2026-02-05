"""List all component categories in Grasshopper."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any


@mcp.tool()
def list_component_categories(ctx: Context) -> Dict[str, Any]:
    """
    List all component categories available in Grasshopper.
    Use this to discover available categories before searching for specific components.

    Returns:
    - category_count: Number of categories
    - categories: List of categories with name, component_count, and subcategories

    Example:
        result = list_component_categories()
        for cat in result["categories"]:
            print(f"{cat['category']}: {cat['component_count']} components")
            print(f"  Subcategories: {', '.join(cat['subcategories'])}")
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command("list_component_categories", {})
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        return {"success": False, "message": str(e)}
