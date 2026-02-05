"""Get a parameter value from a Grasshopper component."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def get_parameter_value(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    output_index: int = 0,
    output_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the current value from a component's output parameter.

    Parameters:
    - instance_id: GUID of the component
    - nickname: Nickname of the component (alternative to instance_id)
    - output_index: Index of the output parameter (default: 0)
    - output_name: Name of the output parameter (alternative to output_index)

    At least one of instance_id or nickname must be provided.

    Returns:
    - component_id: GUID of the component
    - output_name: Name of the output parameter
    - value: The current value (may be a single value or list)
    - data_type: Type of the data
    - item_count: Number of items in the output

    Example:
        # Get value from a number slider
        result = get_parameter_value(nickname="MySlider")
        print(f"Slider value: {result['value']}")

        # Get circle curve output
        result = get_parameter_value(nickname="MyCircle", output_name="Circle")
    """
    try:
        if not instance_id and not nickname:
            return {"success": False, "message": "Either instance_id or nickname is required"}

        gh = get_grasshopper_connection()
        params = {"output_index": output_index}
        if instance_id:
            params["instance_id"] = instance_id
        if nickname:
            params["nickname"] = nickname
        if output_name:
            params["output_name"] = output_name

        return gh.send_command("get_parameter_value", params)
    except Exception as e:
        logger.error(f"Error getting parameter value: {str(e)}")
        return {"success": False, "message": str(e)}
