from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
import json
from rhinomcp import get_rhino_connection, mcp, logger

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_selected_objects_info(ctx: Context, include_attributes: bool = False) -> str:
    """Get detailed information about the currently selected objects in Rhino
    
    Parameters:
    - include_attributes: Whether to include the custom user attributes of the objects in the response
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("get_selected_objects_info", {"include_attributes": include_attributes})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting selected objects from Rhino: {str(e)}")
        return f"Error getting selected objects: {str(e)}"

