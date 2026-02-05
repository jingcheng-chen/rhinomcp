"""Get detailed information about a specific component."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def get_component_info(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific component.

    Parameters:
    - instance_id: GUID of the component instance
    - nickname: Nickname of the component (alternative to instance_id)

    At least one of instance_id or nickname must be provided.

    Returns:
    - instance_id: GUID of the component
    - name: Full name of the component
    - nickname: Nickname
    - category: Category
    - subcategory: Subcategory
    - description: Component description
    - position: [x, y] position on canvas
    - inputs: List of input parameters with names, types, and connection info
    - outputs: List of output parameters with names, types, and data info
    - runtime_message_level: Error/Warning/Blank status
    - runtime_messages: Any error or warning messages

    Example:
        info = get_component_info(nickname="MyCircle")
        print(f"Inputs: {[i['name'] for i in info['inputs']]}")
        print(f"Outputs: {[o['name'] for o in info['outputs']]}")
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

        return gh.send_command("get_component_info", params)
    except Exception as e:
        logger.error(f"Error getting component info: {str(e)}")
        return {"success": False, "message": str(e)}
