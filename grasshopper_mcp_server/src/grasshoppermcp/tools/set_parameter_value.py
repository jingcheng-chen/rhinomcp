"""Set a parameter value on a Grasshopper component."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional, Union, List


@mcp.tool()
def set_parameter_value(
    ctx: Context,
    value: Union[float, int, str, bool, List[Any]],
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    input_index: int = 0,
    input_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set a value on a component's input parameter.

    Parameters:
    - value: The value to set (number, string, boolean, or list)
    - instance_id: GUID of the component
    - nickname: Nickname of the component (alternative to instance_id)
    - input_index: Index of the input parameter (default: 0)
    - input_name: Name of the input parameter (alternative to input_index)

    At least one of instance_id or nickname must be provided.

    Returns:
    - component_id: GUID of the component
    - input_name: Name of the input parameter that was set
    - value: The value that was set
    - message: Confirmation message

    Example:
        # Set a number slider value
        set_parameter_value(nickname="MySlider", value=42.5)

        # Set panel text
        set_parameter_value(nickname="MyPanel", value="Hello World")

        # Set by input name
        set_parameter_value(nickname="MyCircle", input_name="Radius", value=10.0)
    """
    try:
        if not instance_id and not nickname:
            return {"success": False, "message": "Either instance_id or nickname is required"}

        gh = get_grasshopper_connection()
        params = {
            "value": value,
            "input_index": input_index
        }
        if instance_id:
            params["instance_id"] = instance_id
        if nickname:
            params["nickname"] = nickname
        if input_name:
            params["input_name"] = input_name

        result = gh.send_command("set_parameter_value", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error setting parameter value: {str(e)}")
        return {"success": False, "message": str(e)}
