from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, Dict, List


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def measure_objects(
    ctx: Context,
    object_ids: List[str],
) -> Dict[str, Any]:
    """
    Report the spatial relationship between two objects.

    Parameters:
    - object_ids: Exactly two object GUIDs to measure between.

    Returns:
    - object_a, object_b: the two object GUIDs
    - clash: whether the two objects intersect
    - intersection_count: number of intersections (brep curves+points, or curve
      events); 0 for the bbox method
    - bbox_gap: exact minimum distance between the two bounding boxes (0 if they
      meet or overlap), a lower bound on the true surface-to-surface distance
    - method: how clash was determined ("brep", "curve", or "bbox"). "bbox"
      means the pair has no exact pairwise intersection here and overlap was
      judged by bounding box, so read it as approximate.
    """
    if object_ids is None or len(object_ids) != 2:
        raise ValueError(
            "measure_objects requires object_ids with exactly two object ids."
        )

    rhino = get_rhino_connection()
    return rhino.send_command("measure_objects", {"object_ids": object_ids})
