from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
import json
from rhinomcp import get_rhino_connection, mcp, logger
from typing import Dict, Any

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_object_info(ctx: Context, id: str = None, name: str = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific object in the Rhino document.
    The information contains the object's id, name, type, all custom user attributes and geometry info.
    You can either provide the id or the object_name of the object to get information about.
    If both are provided, the id will be used.

    Returns:
    - A dictionary containing the object's information
    - The dictionary will have the following keys:
        - "id": The id of the object
        - "name": The name of the object
        - "type": The type of the object
        - "layer": The layer of the object
        - "material": The material of the object
        - "color": The color of the object
        - "bounding_box": The bounding box of the object
        - "geometry": The geometry info of the object
        - "attributes": A dictionary containing all custom user attributes of the object
    
    Parameters:
    - id: The id of the object to get information about
    - name: The name of the object to get information about
    """
    try:
        rhino = get_rhino_connection()
        params = {}
        if id:
            params["id"] = id
        elif name:
            params["name"] = name
        return rhino.send_command("get_object_info", params)

    except Exception as e:
        logger.error(f"Error getting object info from Rhino: {str(e)}")
        return {
            "error": str(e)
        }
