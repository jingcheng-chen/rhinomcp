"""
Curve operations for advanced geometry manipulation.

These tools provide interfaces for:
- Project Curve: Project a curve onto surfaces or meshes
- Intersect Curves: Find intersections between two curves
- Split Curve: Split a curve at parameters or points
"""

from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import List, Optional, Dict, Any


@mcp.tool()
def project_curve(
    ctx: Context,
    curve_id: str,
    target_ids: List[str],
    direction: List[float],
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Project a curve onto surfaces, polysurfaces, or meshes.

    Parameters:
    - curve_id: The curve ID (GUID) to project
    - target_ids: List of surface, polysurface, or mesh IDs to project onto
    - direction: Projection direction as [x, y, z] vector
    - name: Optional name for the resulting curves

    Returns:
    - Dictionary with result_ids (list of created curve IDs) and message
    """
    try:
        if len(direction) != 3:
            return {"success": False, "message": "Direction must be [x, y, z] vector"}
        if not target_ids:
            return {"success": False, "message": "At least one target ID is required"}

        rhino = get_rhino_connection()
        params = {
            "curve_id": curve_id,
            "target_ids": target_ids,
            "direction": direction,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("project_curve", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Curve projected successfully")
        }
    except Exception as e:
        logger.error(f"Error in project_curve: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def intersect_curves(
    ctx: Context,
    curve_id_a: str,
    curve_id_b: str,
    tolerance: Optional[float] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find intersection points or curves between two curves.

    Parameters:
    - curve_id_a: The first curve ID
    - curve_id_b: The second curve ID
    - tolerance: Optional intersection tolerance (defaults to document tolerance)
    - name: Optional base name for created intersection objects

    Returns:
    - Dictionary with point_ids, curve_ids, and message
    """
    try:
        rhino = get_rhino_connection()
        params = {
            "curve_id_a": curve_id_a,
            "curve_id_b": curve_id_b,
        }
        if tolerance is not None:
            params["tolerance"] = tolerance
        if name:
            params["name"] = name

        result = rhino.send_command("intersect_curves", params)
        return {
            "success": True,
            "point_ids": result.get("point_ids", []),
            "curve_ids": result.get("curve_ids", []),
            "points": result.get("points", []),
            "message": result.get("message", "Intersections found")
        }
    except Exception as e:
        logger.error(f"Error in intersect_curves: {str(e)}")
        return {"success": False, "message": str(e)}


@mcp.tool()
def split_curve(
    ctx: Context,
    curve_id: str,
    parameters: Optional[List[float]] = None,
    point_ids: Optional[List[str]] = None,
    delete_source: bool = True,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Split a curve at specified parameters or points.

    Parameters:
    - curve_id: The curve ID to split
    - parameters: Optional list of curve parameters to split at
    - point_ids: Optional list of point object IDs to split at (closest points on curve will be used)
    - delete_source: Whether to delete the original curve (default: True)
    - name: Optional name for the resulting curve segments

    Returns:
    - Dictionary with result_ids (list of created curve segment IDs) and message
    """
    try:
        if not parameters and not point_ids:
            return {"success": False, "message": "Either parameters or point_ids must be provided"}

        rhino = get_rhino_connection()
        params = {
            "curve_id": curve_id,
            "delete_source": delete_source,
        }
        if parameters:
            params["parameters"] = parameters
        if point_ids:
            params["point_ids"] = point_ids
        if name:
            params["name"] = name

        result = rhino.send_command("split_curve", params)
        return {
            "success": True,
            "result_ids": result.get("result_ids", []),
            "message": result.get("message", "Curve split successfully")
        }
    except Exception as e:
        logger.error(f"Error in split_curve: {str(e)}")
        return {"success": False, "message": str(e)}
