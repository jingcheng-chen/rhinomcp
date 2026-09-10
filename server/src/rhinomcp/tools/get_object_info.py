from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations
from rhinomcp import get_rhino_connection, mcp, logger
from typing import Dict, Any

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_object_info(ctx: Context, id: str = None, name: str = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific object in the Rhino document.
    The information contains the object's id, name, type, all custom user attributes and geometry info.
    Provide at least one selector: id or name of the object to get information about.
    If both are provided, id takes priority.
    If neither selector is known, use get_objects first to discover objects and their ids or names.

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
