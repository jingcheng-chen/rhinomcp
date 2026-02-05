"""Expire a component or the entire Grasshopper solution."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def expire_solution(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None
) -> Dict[str, Any]:
    """
    Expire a specific component or the entire solution to trigger recomputation.

    Parameters:
    - instance_id: GUID of the component to expire (optional)
    - nickname: Nickname of the component to expire (optional)

    If no component is specified, the entire solution is expired.

    Returns:
    - message: Confirmation message
    - expired_component: ID of the expired component (if specific component)

    Example:
        # Expire a specific component
        expire_solution(nickname="MyCircle")

        # Expire the entire solution
        expire_solution()
    """
    try:
        gh = get_grasshopper_connection()
        params = {}
        if instance_id:
            params["instance_id"] = instance_id
        if nickname:
            params["nickname"] = nickname

        result = gh.send_command("expire_solution", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error expiring solution: {str(e)}")
        return {"success": False, "message": str(e)}
