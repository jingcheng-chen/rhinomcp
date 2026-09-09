from mcp.server.mcpserver import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import List, Optional


@mcp.tool()
def boolean_union(
    ctx: Context,
    object_ids: List[str],
    delete_sources: bool = True,
    name: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Perform a boolean union on multiple solid objects, combining them into one.

    Parameters:
    - object_ids: List of object IDs (GUIDs) to union together (minimum 2)
    - delete_sources: Whether to delete the source objects after union (default: True)
    - name: Optional name for the resulting object
    - dry_run: Preview the result and its metrics without modifying the document (default: False)

    Returns:
    A message indicating the result of the operation.

    Note: Objects must be valid closed solids (Breps, Extrusions, or Surfaces).
    """
    try:
        rhino = get_rhino_connection()
        params = {
            "object_ids": object_ids,
            "delete_sources": delete_sources,
            "dry_run": dry_run,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("boolean_union", params)
        if dry_run:
            return f"{result['message']}. Predicted results: {result['results']}"
        return f"{result['message']}. Result IDs: {result['result_ids']}"
    except Exception as e:
        logger.error(f"Error in boolean union: {str(e)}")
        raise


@mcp.tool()
def boolean_difference(
    ctx: Context,
    base_id: str,
    subtract_ids: List[str],
    delete_sources: bool = True,
    name: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Perform a boolean difference (subtraction) - subtract objects from a base object.

    Parameters:
    - base_id: The object ID (GUID) of the base object to subtract from
    - subtract_ids: List of object IDs (GUIDs) to subtract from the base
    - delete_sources: Whether to delete the source objects after operation (default: True)
    - name: Optional name for the resulting object
    - dry_run: Preview the result and its metrics without modifying the document (default: False)

    Returns:
    A message indicating the result of the operation.

    Note: Objects must be valid closed solids (Breps, Extrusions, or Surfaces).
    """
    try:
        rhino = get_rhino_connection()
        params = {
            "base_id": base_id,
            "subtract_ids": subtract_ids,
            "delete_sources": delete_sources,
            "dry_run": dry_run,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("boolean_difference", params)
        if dry_run:
            return f"{result['message']}. Predicted results: {result['results']}"
        return f"{result['message']}. Result IDs: {result['result_ids']}"
    except Exception as e:
        logger.error(f"Error in boolean difference: {str(e)}")
        raise


@mcp.tool()
def boolean_intersection(
    ctx: Context,
    object_ids: List[str],
    delete_sources: bool = True,
    name: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Perform a boolean intersection - keep only the overlapping volume of objects.

    Parameters:
    - object_ids: List of object IDs (GUIDs) to intersect (minimum 2)
    - delete_sources: Whether to delete the source objects after operation (default: True)
    - name: Optional name for the resulting object
    - dry_run: Preview the result and its metrics without modifying the document (default: False)

    Returns:
    A message indicating the result of the operation.

    Note: Objects must be valid closed solids (Breps, Extrusions, or Surfaces) that overlap.
    """
    try:
        rhino = get_rhino_connection()
        params = {
            "object_ids": object_ids,
            "delete_sources": delete_sources,
            "dry_run": dry_run,
        }
        if name:
            params["name"] = name

        result = rhino.send_command("boolean_intersection", params)
        if dry_run:
            return f"{result['message']}. Predicted results: {result['results']}"
        return f"{result['message']}. Result IDs: {result['result_ids']}"
    except Exception as e:
        logger.error(f"Error in boolean intersection: {str(e)}")
        raise
