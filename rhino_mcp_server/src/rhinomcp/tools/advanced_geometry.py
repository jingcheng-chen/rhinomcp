"""
Advanced geometry tools for common operations that would otherwise require RhinoScript.

These tools provide a simple, hallucination-free interface for:
- Loft: Create surface from multiple curves
- Extrude: Extend a curve along a direction
- Sweep1: Sweep profiles along a rail curve
- Offset: Offset a curve by a distance
- Pipe: Create a pipe along a curve
"""

from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import List, Optional, Dict, Any


@mcp.tool()
def loft(
    ctx: Context,
    curve_ids: List[str],
    name: Optional[str] = None,
    closed: bool = False,
    loft_type: int = 0,
) -> Dict[str, Any]:
    """
    Create a loft surface through multiple curves.

    Parameters:
    - curve_ids: List of curve IDs (GUIDs) to loft through (minimum 2 curves).
                 Curves should be in order from start to end of the loft.
    - name: Optional name for the resulting surface
    - closed: If True, creates a closed loft (connects last curve back to first)
    - loft_type: Type of loft (0=Normal, 1=Loose, 2=Tight, 3=Straight, 4=Developable)

    Returns:
    - Dictionary with result_ids (list of created surface IDs) and message

    Example:
        # Create two circles and loft between them
        circle1 = create_object(type="CIRCLE", params={"center": [0,0,0], "radius": 5})
        circle2 = create_object(type="CIRCLE", params={"center": [0,0,10], "radius": 3})
        result = loft(curve_ids=[circle1_id, circle2_id], name="my_loft")
    """
    try:
        if len(curve_ids) < 2:
            return {"success": False, "message": "Loft requires at least 2 curves"}

        rhino = get_rhino_connection()
        params = {
            "curve_ids": curve_ids,
            "closed": closed,
            "loft_type": loft_type,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("loft", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Loft created successfully")
        }
    except Exception as e:
        logger.error(f"Error in loft: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def extrude_curve(
    ctx: Context,
    curve_id: str,
    direction: List[float],
    name: Optional[str] = None,
    cap: bool = True,
) -> Dict[str, Any]:
    """
    Extrude a curve along a direction vector to create a surface or solid.

    Parameters:
    - curve_id: The curve ID (GUID) to extrude
    - direction: Extrusion direction as [x, y, z] vector (e.g., [0, 0, 10] for 10 units up)
    - name: Optional name for the resulting object
    - cap: If True and curve is closed, caps the ends to create a solid (default: True)

    Returns:
    - Dictionary with result_id (created object ID) and message

    Example:
        # Create a circle and extrude it upward to make a cylinder
        circle = create_object(type="CIRCLE", params={"center": [0,0,0], "radius": 5})
        result = extrude_curve(curve_id=circle_id, direction=[0, 0, 10], name="cylinder")
    """
    try:
        if len(direction) != 3:
            return {"success": False, "message": "Direction must be [x, y, z] vector"}

        rhino = get_rhino_connection()
        params = {
            "curve_id": curve_id,
            "direction": direction,
            "cap": cap,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("extrude_curve", params)
        return {
            "success": True,
            "result_id": result.get("result_id"),
            "message": result.get("message", "Extrusion created successfully")
        }
    except Exception as e:
        logger.error(f"Error in extrude_curve: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def sweep1(
    ctx: Context,
    rail_id: str,
    profile_ids: List[str],
    name: Optional[str] = None,
    closed: bool = False,
) -> Dict[str, Any]:
    """
    Sweep one or more profile curves along a rail curve.

    Parameters:
    - rail_id: The rail curve ID (GUID) - the path along which to sweep
    - profile_ids: List of profile curve IDs (GUIDs) - the shapes to sweep
    - name: Optional name for the resulting surface
    - closed: If True, creates a closed sweep

    Returns:
    - Dictionary with result_ids (list of created surface IDs) and message

    Example:
        # Create a rail (line) and profile (circle), then sweep
        rail = create_object(type="LINE", params={"start": [0,0,0], "end": [10,0,5]})
        profile = create_object(type="CIRCLE", params={"center": [0,0,0], "radius": 1})
        result = sweep1(rail_id=rail_id, profile_ids=[profile_id], name="swept_tube")
    """
    try:
        if not profile_ids:
            return {"success": False, "message": "Sweep requires at least 1 profile curve"}

        rhino = get_rhino_connection()
        params = {
            "rail_id": rail_id,
            "profile_ids": profile_ids,
            "closed": closed,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("sweep1", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Sweep created successfully")
        }
    except Exception as e:
        logger.error(f"Error in sweep1: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def offset_curve(
    ctx: Context,
    curve_id: str,
    distance: float,
    name: Optional[str] = None,
    plane: Optional[List[float]] = None,
    corner_style: int = 1,
) -> Dict[str, Any]:
    """
    Offset a curve by a specified distance.

    Parameters:
    - curve_id: The curve ID (GUID) to offset
    - distance: Offset distance (positive = one side, negative = other side)
    - name: Optional name for the resulting curve
    - plane: Optional plane normal [x, y, z] for the offset direction.
             If not provided, uses the curve's plane or world XY.
    - corner_style: How to handle corners (0=None, 1=Sharp, 2=Round, 3=Smooth, 4=Chamfer)

    Returns:
    - Dictionary with result_ids (list of created curve IDs) and message

    Example:
        # Offset a curve by 2 units
        result = offset_curve(curve_id=my_curve_id, distance=2.0, name="offset_curve")
    """
    try:
        rhino = get_rhino_connection()
        params = {
            "curve_id": curve_id,
            "distance": distance,
            "corner_style": corner_style,
        }
        if name:
            params["name"] = name
        if plane:
            params["plane"] = plane

        result = rhino.send_command("offset_curve", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Offset created successfully")
        }
    except Exception as e:
        logger.error(f"Error in offset_curve: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def pipe(
    ctx: Context,
    curve_id: str,
    radius: float,
    name: Optional[str] = None,
    cap: bool = True,
    fit_rail: bool = False,
) -> Dict[str, Any]:
    """
    Create a pipe (tube) along a curve.

    Parameters:
    - curve_id: The curve ID (GUID) to create pipe along
    - radius: Radius of the pipe
    - name: Optional name for the resulting object
    - cap: If True, caps the ends of the pipe (default: True)
    - fit_rail: If True, fits the pipe more closely to the rail curve

    Returns:
    - Dictionary with result_ids (list of created object IDs) and message

    Example:
        # Create a curved line and make it into a pipe
        curve = create_object(type="ARC", params={"center": [0,0,0], "radius": 10, "start_angle": 0, "end_angle": 90})
        result = pipe(curve_id=curve_id, radius=0.5, name="pipe_tube")
    """
    try:
        if radius <= 0:
            return {"success": False, "message": "Radius must be positive"}

        rhino = get_rhino_connection()
        params = {
            "curve_id": curve_id,
            "radius": radius,
            "cap": cap,
            "fit_rail": fit_rail,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("pipe", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Pipe created successfully")
        }
    except Exception as e:
        logger.error(f"Error in pipe: {str(e)}")
        return {"success": False, "message": str(e)}
