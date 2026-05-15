from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger


@mcp.tool()
def delete_object(ctx: Context, id: str = None, name: str = None, all: bool = None) -> str:
    """
    Delete an object from the Rhino document.

    Parameters:
    - id: The id of the object to delete
    - name: The name of the object to delete
    - all: If True, delete every object in the document.

    Exactly one of id, name, or all=True must be provided.
    """
    selectors = [v for v in (id, name, True if all else None) if v]
    if not selectors:
        return "Error deleting object: must specify id, name, or all=True."
    if len(selectors) > 1:
        return "Error deleting object: specify exactly one of id, name, or all=True."

    try:
        rhino = get_rhino_connection()

        commandParams = {}
        if id is not None:
            commandParams["id"] = id
        if name is not None:
            commandParams["name"] = name
        if all:
            commandParams["all"] = True

        result = rhino.send_command("delete_object", commandParams)

        if all:
            count = result.get("count")
            if count is not None:
                return f"Deleted all objects ({count})."
            return "Deleted all objects."
        return f"Deleted object: {result.get('name') or result.get('id')}"
    except Exception as e:
        logger.error(f"Error deleting object: {str(e)}")
        return f"Error deleting object: {str(e)}"