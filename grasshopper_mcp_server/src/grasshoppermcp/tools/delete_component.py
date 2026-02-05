"""Delete a component from the Grasshopper canvas."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def delete_component(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a component from the Grasshopper canvas.

    Parameters:
    - instance_id: GUID of the component instance to delete
    - nickname: Nickname of the component to delete (alternative to instance_id)

    At least one of instance_id or nickname must be provided.

    Returns:
    - deleted_id: GUID of the deleted component
    - name: Name of the deleted component
    - message: Confirmation message

    Example:
        # Delete by instance ID
        delete_component(instance_id="a1b2c3d4-...")

        # Delete by nickname
        delete_component(nickname="MyCircle")
    """
    try:
        if not instance_id and not nickname:
            return {"success": False, "message": "Either instance_id or nickname is required"}

        gh = get_grasshopper_connection()
        params = {}
        if instance_id:
            params["instance_id"] = instance_id
        if nickname:
            params["nickname"] = nickname

        result = gh.send_command("delete_component", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error deleting component: {str(e)}")
        return {"success": False, "message": str(e)}
