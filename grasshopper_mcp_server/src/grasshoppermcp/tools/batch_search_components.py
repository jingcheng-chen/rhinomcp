"""Batch search for multiple components at once."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, List


@mcp.tool()
def batch_search_components(
    ctx: Context,
    queries: List[str]
) -> Dict[str, Any]:
    """
    Search for multiple components at once. Much more efficient than calling
    search_components multiple times.

    IMPORTANT: Before using this, read the grasshopper://components/reference resource
    which contains most common component names. Only search for components not in that list.

    Parameters:
    - queries: List of component names to search for (e.g., ["Circle", "Loft", "Move"])

    Returns:
    - results: Dict mapping each query to its best match (or null if not found)
    - found_count: Number of queries that found matches
    - not_found: List of queries that had no matches

    Example:
        result = batch_search_components(queries=["Circle", "Loft", "Move", "Extrude"])
        # Returns: {"results": {"Circle": {...}, "Loft": {...}, ...}, "found_count": 4}
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command("batch_search_components", {"queries": queries})
    except Exception as e:
        logger.error(f"Error batch searching components: {str(e)}")
        return {"success": False, "message": str(e)}
