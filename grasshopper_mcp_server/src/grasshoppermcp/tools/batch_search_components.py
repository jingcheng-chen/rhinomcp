"""Batch search for multiple components at once."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, List


@mcp.tool()
def batch_search_components(
    ctx: Context,
    queries: List[str]
) -> Dict[str, Any]:
    """
    Search for multiple components at once. Only use for UNCOMMON components!

    These common components DON'T need searching - use directly in create_definition:
    - Inputs: "Number Slider", "Panel", "Boolean Toggle"
    - Points: "Point", "Construct Point", "Deconstruct Point"
    - Curves: "Line", "Circle", "Arc", "Rectangle", "Polyline", "Interpolate"
    - Surfaces: "Extrude", "Loft", "Sweep1", "Pipe", "Boundary Surfaces"
    - Math: "Addition", "Multiplication", "Division", "Series", "Range"
    - Trig: "Sine", "Cosine", "Tangent"
    - Vectors: "Unit X", "Unit Y", "Unit Z", "Vector XYZ", "Amplitude"
    - Transform: "Move", "Rotate", "Scale", "Mirror"
    - Data: "Cross Reference", "Merge", "Flatten", "Graft", "List Item"
    - Analysis: "Area", "Volume", "Evaluate Curve", "Divide Curve"
    - Boolean: "Solid Union", "Solid Difference", "Solid Intersection"

    Only search for unusual components like third-party plugins.

    Parameters:
    - queries: List of UNCOMMON component names to search for

    Returns:
    - results: Dict mapping each query to its best match
    - not_found: List of queries that had no matches
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command("batch_search_components", {"queries": queries})
    except Exception as e:
        logger.error(f"Error batch searching components: {str(e)}")
        return {"success": False, "message": str(e)}
