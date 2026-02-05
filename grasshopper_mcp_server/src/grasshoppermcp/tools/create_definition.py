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
    Create a complete Grasshopper definition with components, connections, and values in one batch operation.

    This is the recommended way to create complex definitions as it:
    - Creates everything in a single atomic operation
    - Automatically resolves component references by nickname
    - Provides detailed error reporting for each step

    Parameters:
    - components: List of components to create. Each component should have:
        - name: Component name (e.g., "Circle", "Extrude", "Number Slider")
        - nickname: Unique nickname for referencing (required for connections)
        - position: [x, y] position on canvas (optional, default: [0, 0])

    - connections: List of connections to create. Each connection should have:
        - source: Nickname of source component
        - source_output: Output parameter index (default: 0)
        - target: Nickname of target component
        - target_input: Input parameter index (default: 0)

    - values: List of values to set. Each value should have:
        - component: Nickname of the component
        - input: Input parameter index or name
        - value: The value to set (number, string, boolean, array, or point [x,y,z])

    - clear_canvas: If true, clear all existing components before creating new ones

    Returns:
    - components_created: Number of components created
    - connections_created: Number of connections made
    - values_set: Number of values set
    - error_count: Number of errors encountered
    - components: Details of created components with instance_ids
    - connections: Details of created connections
    - values: Details of set values
    - errors: List of errors (if any)

    Example - Create a circle and extrude it:
        create_definition(
            components=[
                {"name": "Circle", "nickname": "MyCircle", "position": [0, 0]},
                {"name": "Unit Z", "nickname": "ZDir", "position": [0, 100]},
                {"name": "Extrude", "nickname": "MyExtrude", "position": [200, 50]}
            ],
            connections=[
                {"source": "MyCircle", "source_output": 0, "target": "MyExtrude", "target_input": 0},
                {"source": "ZDir", "source_output": 0, "target": "MyExtrude", "target_input": 1}
            ],
            values=[
                {"component": "MyCircle", "input": "Radius", "value": 10.0}
            ]
        )

    Example - Create a point grid:
        create_definition(
            components=[
                {"name": "Series", "nickname": "XSeries", "position": [0, 0]},
                {"name": "Series", "nickname": "YSeries", "position": [0, 100]},
                {"name": "Cross Reference", "nickname": "CrossRef", "position": [200, 50]},
                {"name": "Point", "nickname": "Points", "position": [400, 50]}
            ],
            connections=[
                {"source": "XSeries", "target": "CrossRef", "target_input": 0},
                {"source": "YSeries", "target": "CrossRef", "target_input": 1},
                {"source": "CrossRef", "source_output": 0, "target": "Points", "target_input": 0},
                {"source": "CrossRef", "source_output": 1, "target": "Points", "target_input": 1}
            ],
            values=[
                {"component": "XSeries", "input": "Count", "value": 10},
                {"component": "XSeries", "input": "Step", "value": 5.0},
                {"component": "YSeries", "input": "Count", "value": 10},
                {"component": "YSeries", "input": "Step", "value": 5.0}
            ]
        )

    Common component names:
    - Primitives: "Point", "Line", "Circle", "Rectangle", "Arc", "Polygon"
    - Surfaces: "Extrude", "Loft", "Sweep1", "Revolution", "Boundary Surfaces"
    - Parameters: "Number Slider", "Panel", "Boolean Toggle", "Point" (Params)
    - Math: "Addition", "Subtraction", "Multiplication", "Division", "Series", "Range"
    - Vectors: "Unit X", "Unit Y", "Unit Z", "Vector XYZ"
    - Lists: "List Item", "List Length", "Merge", "Flatten", "Graft"
    - Transforms: "Move", "Rotate", "Scale", "Mirror", "Orient"
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
