from typing import Any, Dict

from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger


@mcp.tool()
def delete_object(ctx: Context, id: str = None, name: str = None, all: bool = None) -> Dict[str, Any]:
    """
    Delete an object from the Rhino document.

    Parameters:
    - id: The id of the object to delete
    - name: The name of the object to delete
    - all: If True, delete every object in the document.

    Exactly one of id, name, or all=True must be provided. Errors propagate
    as MCP tool errors.
    """
    selectors = [v for v in (id, name, True if all else None) if v]
    if not selectors:
        raise ValueError("delete_object: must specify id, name, or all=True.")
    if len(selectors) > 1:
        raise ValueError("delete_object: specify exactly one of id, name, or all=True.")

    rhino = get_rhino_connection()

    commandParams: Dict[str, Any] = {}
    if id is not None: commandParams["id"] = id
    if name is not None: commandParams["name"] = name
    if all: commandParams["all"] = True

    result = rhino.send_command("delete_object", commandParams)

    if all:
        count = result.get("count")
        return {
            "success": True,
            "scope": "all",
            "count": count,
            "message": f"Deleted all objects ({count})." if count is not None else "Deleted all objects.",
        }
    return {
        "success": True,
        "id": result.get("id"),
        "name": result.get("name"),
        "message": f"Deleted object: {result.get('name') or result.get('id')}",
    }
