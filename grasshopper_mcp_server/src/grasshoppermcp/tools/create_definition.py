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
    BUILD EVERYTHING IN ONE CALL - sliders, components, AND connections together!

    IMPORTANT: Native GH components can handle complex patterns! No scripts needed.
    Use: Series, Sine, Cosine, Multiplication, Construct Point, Interpolate, Move, etc.

    COMMON COMPONENTS (no search needed):
    - Inputs: "Number Slider", "Panel", "Boolean Toggle"
    - Math: "Addition", "Multiplication", "Division", "Series", "Range", "Sine", "Cosine"
    - Points: "Construct Point", "Deconstruct Point"
    - Vectors: "Unit X", "Unit Y", "Unit Z", "Vector XYZ", "Amplitude"
    - Curves: "Line", "Circle", "Arc", "Polyline", "Interpolate"
    - Surfaces: "Extrude", "Loft", "Sweep1", "Pipe"
    - Transform: "Move", "Rotate", "Scale"
    - Data: "Merge", "Graft", "Flatten", "Cross Reference"

    Parameters:
    - components: List of {name, nickname, position, ...slider props}
    - connections: List of {source, target, source_output, target_input}
    - values: List of {component, input, value} for non-slider inputs
    - clear_canvas: bool to clear existing components

    Returns: has_errors, runtime_errors, components_created, connections_created

    COMPLETE EXAMPLE - Parametric Wavy Facade (ALL in one call!):
        create_definition(
            clear_canvas=True,
            components=[
                # Sliders for parameters
                {"name": "Number Slider", "nickname": "FinCount", "position": [0, 0],
                 "min": 5, "max": 50, "value": 20, "decimals": 0},
                {"name": "Number Slider", "nickname": "FinSpacing", "position": [0, 60],
                 "min": 0.5, "max": 3, "value": 1},
                {"name": "Number Slider", "nickname": "Height", "position": [0, 120],
                 "min": 5, "max": 30, "value": 15},
                {"name": "Number Slider", "nickname": "WaveAmp", "position": [0, 180],
                 "min": 0.5, "max": 5, "value": 2},
                {"name": "Number Slider", "nickname": "WaveFreq", "position": [0, 240],
                 "min": 0.1, "max": 1, "value": 0.3},
                {"name": "Number Slider", "nickname": "Thickness", "position": [0, 300],
                 "min": 0.05, "max": 0.5, "value": 0.15},

                # X positions for fins: Series from 0
                {"name": "Series", "nickname": "XPositions", "position": [200, 30]},
                # Z heights: Range from 0 to Height
                {"name": "Construct Domain", "nickname": "HeightDomain", "position": [200, 120]},
                {"name": "Range", "nickname": "ZHeights", "position": [350, 120]},

                # Cross reference X and Z to get grid
                {"name": "Cross Reference", "nickname": "GridXZ", "position": [500, 60]},

                # Calculate wave: sin(x * freq) * amp
                {"name": "Multiplication", "nickname": "XFreq", "position": [650, 0]},
                {"name": "Sine", "nickname": "WaveCalc", "position": [800, 0]},
                {"name": "Multiplication", "nickname": "WaveY", "position": [950, 0]},

                # Build points with wave displacement
                {"name": "Construct Point", "nickname": "WavePoints", "position": [1100, 60]},

                # Create curves through points (one per fin)
                {"name": "Interpolate", "nickname": "FinCurves", "position": [1250, 60]},

                # Extrude curves for thickness
                {"name": "Unit Y", "nickname": "ExtDir", "position": [1250, 150]},
                {"name": "Extrude", "nickname": "FinSurfaces", "position": [1400, 90]}
            ],
            connections=[
                # X positions: Series(0, FinSpacing, FinCount)
                {"source": "FinSpacing", "target": "XPositions", "target_input": 1},
                {"source": "FinCount", "target": "XPositions", "target_input": 2},

                # Height domain and range
                {"source": "Height", "target": "HeightDomain", "target_input": 1},
                {"source": "HeightDomain", "target": "ZHeights", "target_input": 0},

                # Cross reference X and Z
                {"source": "XPositions", "target": "GridXZ", "target_input": 0},
                {"source": "ZHeights", "target": "GridXZ", "target_input": 1},

                # Wave calculation
                {"source": "GridXZ", "target": "XFreq", "source_output": 0, "target_input": 0},
                {"source": "WaveFreq", "target": "XFreq", "target_input": 1},
                {"source": "XFreq", "target": "WaveCalc", "target_input": 0},
                {"source": "WaveCalc", "target": "WaveY", "target_input": 0},
                {"source": "WaveAmp", "target": "WaveY", "target_input": 1},

                # Build points: X from grid, Y from wave, Z from grid
                {"source": "GridXZ", "target": "WavePoints", "source_output": 0, "target_input": 0},
                {"source": "WaveY", "target": "WavePoints", "target_input": 1},
                {"source": "GridXZ", "target": "WavePoints", "source_output": 1, "target_input": 2},

                # Interpolate and extrude
                {"source": "WavePoints", "target": "FinCurves", "target_input": 0},
                {"source": "Thickness", "target": "ExtDir", "target_input": 0},
                {"source": "FinCurves", "target": "FinSurfaces", "target_input": 0},
                {"source": "ExtDir", "target": "FinSurfaces", "target_input": 1}
            ],
            values=[
                {"component": "HeightDomain", "input": 0, "value": 0},
                {"component": "ZHeights", "input": 1, "value": 10}
            ]
        )

    SIMPLE EXAMPLE - Circle and Extrude:
        create_definition(
            components=[
                {"name": "Number Slider", "nickname": "Radius", "min": 1, "max": 50, "value": 10},
                {"name": "Circle", "nickname": "Circ", "position": [200, 0]},
                {"name": "Unit Z", "nickname": "UpVec", "position": [200, 80]},
                {"name": "Extrude", "nickname": "Ext", "position": [400, 40]}
            ],
            connections=[
                {"source": "Radius", "target": "Circ", "target_input": 1},
                {"source": "Circ", "target": "Ext", "target_input": 0},
                {"source": "UpVec", "target": "Ext", "target_input": 1}
            ]
        )
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
