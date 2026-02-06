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
    Set a value on a component. Works with sliders, panels, expressions, and regular inputs.

    SUPPORTED COMPONENTS:
    - Number Slider: set_parameter_value(nickname="Slider", value=50)
      Optional: min, max to adjust range
    - Panel: set_parameter_value(nickname="Panel", value="text")
    - Boolean Toggle: set_parameter_value(nickname="Toggle", value=True)
    - Expression: set_parameter_value(nickname="Expr", value="x*sin(y)")
    - Regular inputs: set_parameter_value(nickname="Circle", input_name="Radius", value=10)

    Parameters:
    - value: The value (number for sliders, string for panels/expressions)
    - nickname: Component nickname (recommended)
    - instance_id: Component GUID (alternative to nickname)
    - input_index: Input parameter index (default: 0)
    - input_name: Input parameter name (alternative to index)

    Examples:
        # Slider - just set value
        set_parameter_value(nickname="RadiusSlider", value=25.5)

        # Slider - also change range
        set_parameter_value(nickname="RadiusSlider", value=75, min=0, max=100)

        # Panel text
        set_parameter_value(nickname="InfoPanel", value="Facade Design v1")

        # Expression formula
        set_parameter_value(nickname="WaveExpr", value="amplitude*sin(x*freq)")

        # Regular component input by name
        set_parameter_value(nickname="MyCircle", input_name="Radius", value=10)
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
