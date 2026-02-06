"""Get type information about a component BEFORE creating it."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
def get_component_type_info(
    ctx: Context,
    name: Optional[str] = None,
    guid: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a component TYPE before creating it.

    Use this to discover what inputs and outputs a component has BEFORE adding it.
    This is especially useful for components you haven't used before.

    Parameters:
    - name: Component name (e.g., "Circle", "Expression", "Loft")
    - guid: Component GUID (alternative to name)

    At least one of name or guid must be provided.

    Returns:
    - name: Full component name
    - category: Component category
    - inputs: List of input parameters with index, name, type, optional flag
    - outputs: List of output parameters with index, name, type
    - input_count: Number of inputs
    - output_count: Number of outputs
    - warnings: Any known issues or gotchas with this component

    IMPORTANT WARNINGS returned for known problematic components:
    - Expression: Has DYNAMIC inputs (only x, y by default). Consider using
      dedicated math components like "Sine", "Cosine", "Tangent" instead.
    - Script components: Inputs/outputs are configurable.

    Example:
        # Check what inputs Circle has before creating
        info = get_component_type_info(name="Circle")
        # Returns: inputs=[{index: 0, name: "Plane"}, {index: 1, name: "Radius"}]

        # Check Expression component (and see warnings)
        info = get_component_type_info(name="Expression")
        # Returns: warnings=["Expression has DYNAMIC inputs..."]

        # Use this info to correctly connect:
        create_definition(
            components=[
                {"name": "Circle", "nickname": "C", "position": [0, 0]}
            ],
            connections=[
                {"source": "Radius", "target": "C", "target_input": 1}  # Radius is input 1
            ]
        )
    """
    try:
        if not name and not guid:
            return {"success": False, "message": "Either name or guid is required"}

        gh = get_grasshopper_connection()
        params = {}
        if name:
            params["name"] = name
        if guid:
            params["guid"] = guid

        return gh.send_command("get_component_type_info", params)
    except Exception as e:
        logger.error(f"Error getting component type info: {str(e)}")
        return {"success": False, "message": str(e)}
