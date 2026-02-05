"""Run the Grasshopper solution."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any


@mcp.tool()
def run_solution(ctx: Context) -> Dict[str, Any]:
    """
    Recompute the entire Grasshopper solution.

    This forces all components to recalculate their outputs.
    Use this after making changes to ensure the definition is up to date.

    Returns:
    - message: Confirmation message
    - duration_ms: Time taken to recompute (if available)

    Example:
        # Run the solution after making changes
        run_solution()
    """
    try:
        gh = get_grasshopper_connection()
        result = gh.send_command("run_solution", {})
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error running solution: {str(e)}")
        return {"success": False, "message": str(e)}
