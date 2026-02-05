"""Get information about the active Grasshopper document."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any


@mcp.tool()
def get_gh_document_info(ctx: Context) -> Dict[str, Any]:
    """
    Get information about the active Grasshopper document.

    Returns:
    - has_document: Whether a GH document is open
    - file_path: Path to the GH file (or "(unsaved)")
    - object_count: Total number of objects on canvas
    - component_count: Number of components
    - parameter_count: Number of standalone parameters
    - group_count: Number of groups
    - components_by_category: Breakdown of components by category

    Example:
        info = get_gh_document_info()
        if info["has_document"]:
            print(f"Document has {info['component_count']} components")
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command("get_gh_document_info", {})
    except Exception as e:
        logger.error(f"Error getting GH document info: {str(e)}")
        return {"success": False, "message": str(e)}
