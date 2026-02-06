"""Create a complete Grasshopper definition in one batch operation."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional, List


@mcp.tool()
def create_definition(
    ctx: Context,
    components: List[Dict[str, Any]],
    connections: Optional[List[Dict[str, Any]]] = None,
    values: Optional[List[Dict[str, Any]]] = None,
    clear_canvas: bool = False
) -> Dict[str, Any]:
    """
    Create a complete Grasshopper definition with components, connections, and values.

    IMPORTANT - NO SEARCH NEEDED for common components! Use these names directly:
    - Inputs: "Number Slider", "Panel", "Boolean Toggle"
    - Geometry: "Point", "Line", "Circle", "Rectangle", "Arc", "Polyline"
    - Surfaces: "Extrude", "Loft", "Sweep1", "Pipe", "Boundary Surfaces"
    - Math: "Addition", "Multiplication", "Division", "Series", "Range", "Expression"
    - Vectors: "Unit X", "Unit Y", "Unit Z", "Construct Point"
    - Transform: "Move", "Rotate", "Scale", "Mirror"
    - Lists: "List Item", "Merge", "Flatten", "Graft"

    NUMBER SLIDERS - Fully supported with initial values:
    {"name": "Number Slider", "nickname": "MySlider", "position": [0,0],
     "min": 0, "max": 100, "value": 50, "decimals": 2}

    PANELS - Can set initial content:
    {"name": "Panel", "nickname": "Info", "position": [0,0], "content": "text"}

    Parameters:
    - components: List of components. Each needs:
        - name: Component name (use names above, no search needed)
        - nickname: Unique name for connections
        - position: [x, y] optional
        - For sliders: min, max, value, decimals
        - For panels: content

    - connections: List of wires:
        - source: Source nickname
        - target: Target nickname
        - source_output: Output index (default: 0)
        - target_input: Input index (default: 0)

    - values: Set input values on components (for non-slider components):
        - component: Nickname
        - input: Input index or name
        - value: The value

    Returns (IMPORTANT - check for errors!):
    - has_errors: True if any errors occurred - CHECK THIS FIRST
    - runtime_errors: List of component errors with messages - FIX THESE
    - runtime_warnings: List of warnings
    - message: Summary including any error details

    If has_errors is True, the response includes runtime_errors like:
    {"nickname": "FacadeRect", "name": "Rectangle",
     "messages": ["Data conversion failed from Domain to Rectangle"]}

    Example with sliders:
        result = create_definition(
            components=[
                {"name": "Number Slider", "nickname": "Radius", "position": [0,0],
                 "min": 1, "max": 50, "value": 10},
                {"name": "Circle", "nickname": "Circ", "position": [200,0]},
                {"name": "Extrude", "nickname": "Ext", "position": [400,40]}
            ],
            connections=[
                {"source": "Radius", "target": "Circ", "target_input": 1}
            ]
        )
        # ALWAYS check for errors:
        if result.get("has_errors"):
            # Fix the runtime_errors before proceeding
            print(result["runtime_errors"])
    """
    try:
        if not components:
            return {"success": False, "message": "At least one component is required"}

        gh = get_grasshopper_connection()
        params = {
            "components": components,
            "connections": connections or [],
            "values": values or [],
            "clear_canvas": clear_canvas
        }

        result = gh.send_command("create_definition", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error creating definition: {str(e)}")
        return {"success": False, "message": str(e)}
