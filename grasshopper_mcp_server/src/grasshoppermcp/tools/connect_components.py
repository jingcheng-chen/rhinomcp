"""Connect two components on the Grasshopper canvas."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def connect_components(
    ctx: Context,
    source_instance_id: Optional[str] = None,
    source_nickname: Optional[str] = None,
    source_output: int = 0,
    target_instance_id: Optional[str] = None,
    target_nickname: Optional[str] = None,
    target_input: int = 0
) -> Dict[str, Any]:
    """
    Connect an output of one component to an input of another component.

    Parameters:
    - source_instance_id: GUID of the source component
    - source_nickname: Nickname of source component (alternative to instance_id)
    - source_output: Index of the output parameter (default: 0)
    - target_instance_id: GUID of the target component
    - target_nickname: Nickname of target component (alternative to instance_id)
    - target_input: Index of the input parameter (default: 0)

    At least one identifier (instance_id or nickname) is required for both source and target.

    Returns:
    - source_id: GUID of the source component
    - target_id: GUID of the target component
    - source_param: Name of the output parameter
    - target_param: Name of the input parameter
    - message: Confirmation message

    Example:
        # Connect Circle output to Extrude input
        connect_components(
            source_nickname="MyCircle",
            source_output=0,
            target_nickname="MyExtrude",
            target_input=0
        )
    """
    try:
        if not source_instance_id and not source_nickname:
            return {"success": False, "message": "Either source_instance_id or source_nickname is required"}
        if not target_instance_id and not target_nickname:
            return {"success": False, "message": "Either target_instance_id or target_nickname is required"}

        gh = get_grasshopper_connection()
        params = {
            "source_output": source_output,
            "target_input": target_input
        }
        if source_instance_id:
            params["source_instance_id"] = source_instance_id
        if source_nickname:
            params["source_nickname"] = source_nickname
        if target_instance_id:
            params["target_instance_id"] = target_instance_id
        if target_nickname:
            params["target_nickname"] = target_nickname

        result = gh.send_command("connect_components", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error connecting components: {str(e)}")
        return {"success": False, "message": str(e)}
