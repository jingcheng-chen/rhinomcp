from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, List, Dict, Optional


@mcp.tool()
def modify_object(
    ctx: Context,
    id: Optional[str] = None,
    name: Optional[str] = None,
    new_name: Optional[str] = None,
    new_color: Optional[List[int]] = None,
    translation: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    visible: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Modify an existing object in the Rhino document.

    Parameters:
    - id: The id of the object to modify
    - name: The name of the object to modify
    - new_name: Optional new name for the object
    - new_color: Optional [r, g, b] color values (0-255) for the object
    - translation: Optional [x, y, z] translation vector
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale factors
    - visible: Optional boolean to set visibility

    Returns a dict with success, id, name, message, plus bounding_box — the
    object's new post-edit axis-aligned extent — and, for curve-like types,
    geometry, each present only when the plugin reported it. Errors propagate
    as MCP tool errors.
    """
    rhino = get_rhino_connection()

    params: Dict[str, Any] = {}
    if id is not None: params["id"] = id
    if name is not None: params["name"] = name
    if new_name is not None: params["new_name"] = new_name
    if new_color is not None: params["new_color"] = new_color
    if translation is not None: params["translation"] = translation
    if rotation is not None: params["rotation"] = rotation
    if scale is not None: params["scale"] = scale
    if visible is not None: params["visible"] = visible

    result = rhino.send_command("modify_object", params)
    response: Dict[str, Any] = {
        "success": True,
        "id": result.get("id"),
        "name": result.get("name"),
        "message": f"Modified object: {result.get('name')}",
    }
    # The plugin re-serializes the object after the edit, so bounding_box here
    # reflects the NEW post-transform extent — exactly what a client needs to
    # confirm a translate/scale landed where intended, without re-querying.
    # geometry (curve-like types) comes along the same way. Each is added only
    # when present to keep the response shape stable.
    if result.get("bounding_box") is not None:
        response["bounding_box"] = result["bounding_box"]
    if result.get("geometry") is not None:
        response["geometry"] = result["geometry"]
    return response