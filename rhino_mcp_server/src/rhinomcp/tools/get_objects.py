from mcp.server.fastmcp import Context
import json
from typing import Optional
from rhinomcp import get_rhino_connection, mcp, logger


@mcp.tool()
def get_objects(
    ctx: Context,
    offset: int = 0,
    limit: int = 50,
    layer_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    bbox_filter: Optional[list] = None,
    include_geometry: bool = True,
) -> str:
    """
    Query objects in the Rhino document with filtering and pagination.

    Use this tool to retrieve specific subsets of objects after first calling
    get_document_summary to understand the model composition.

    Parameters:
    - offset: Number of objects to skip (default: 0)
    - limit: Maximum objects to return (default: 50, max: 200)
    - layer_filter: Return only objects on this layer (name or full path)
    - type_filter: Return only objects of this type:
        POINT, LINE, POLYLINE, CIRCLE, ARC, CURVE,
        BOX, SPHERE, CONE, CYLINDER, SURFACE, BREP, EXTRUSION, MESH
    - bbox_filter: Return objects within bounding box [[min_x,min_y,min_z],[max_x,max_y,max_z]]
    - include_geometry: Include detailed geometry data (default: true, false for lightweight listing)

    Returns:
    - objects: Array of object information
    - total_matching: Total count matching filters
    - offset, limit: Applied pagination
    - has_more: Whether more objects are available
    - filters: The filters that were applied

    Example: Get all curves on layer "Walls":
        get_objects(layer_filter="Walls", type_filter="CURVE")

    Example: Get next page of results:
        get_objects(offset=50, limit=50)
    """
    try:
        rhino = get_rhino_connection()

        params = {
            "offset": offset,
            "limit": limit,
            "include_geometry": include_geometry,
        }

        if layer_filter is not None:
            params["layer_filter"] = layer_filter
        if type_filter is not None:
            params["type_filter"] = type_filter.upper()
        if bbox_filter is not None:
            params["bbox_filter"] = bbox_filter

        result = rhino.send_command("get_objects", params)
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error getting objects from Rhino: {str(e)}")
        return f"Error getting objects: {str(e)}"
