from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, Dict, List, Optional, Union


UserStringValue = Union[str, int, float, bool, None]


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_object_attributes(
    ctx: Context,
    id: Optional[str] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get lightweight object metadata and custom user strings.

    Parameters:
    - id: The id of the object to inspect
    - name: The name of the object to inspect

    Returns:
    A dictionary containing object name, layer, color/material sources,
    visibility/lock state, and user_strings. If both id and name are provided,
    id is used.
    """
    rhino = get_rhino_connection()

    params: Dict[str, Any] = {}
    if id is not None:
        params["id"] = id
    elif name is not None:
        params["name"] = name

    return rhino.send_command("get_object_attributes", params)


@mcp.tool()
def update_object_attributes(
    ctx: Context,
    id: Optional[str] = None,
    name: Optional[str] = None,
    new_name: Optional[str] = None,
    layer: Optional[str] = None,
    color: Optional[List[int]] = None,
    material_index: Optional[int] = None,
    visible: Optional[bool] = None,
    locked: Optional[bool] = None,
    user_strings: Optional[Dict[str, UserStringValue]] = None,
    delete_user_strings: Optional[List[str]] = None,
    clear_user_strings: bool = False,
) -> Dict[str, Any]:
    """
    Update lightweight object metadata and custom user strings.

    Parameters:
    - id: The id of the object to update
    - name: The name of the object to update
    - new_name: Optional new object name
    - layer: Optional destination layer name or full path
    - color: Optional RGB color [r, g, b]. Sets color source to object.
    - material_index: Optional Rhino material table index. Sets material source to object.
    - visible: Optional visibility flag. False hides the object.
    - locked: Optional locked flag. True locks the object.
    - user_strings: Optional key/value metadata. Values are stored as strings; null deletes a key.
    - delete_user_strings: Optional list of user-string keys to delete.
    - clear_user_strings: If true, remove all existing user strings before applying updates.

    Returns:
    The updated lightweight object metadata.
    """
    rhino = get_rhino_connection()

    params: Dict[str, Any] = {}
    if id is not None:
        params["id"] = id
    if name is not None:
        params["name"] = name
    if new_name is not None:
        params["new_name"] = new_name
    if layer is not None:
        params["layer"] = layer
    if color is not None:
        params["color"] = color
    if material_index is not None:
        params["material_index"] = material_index
    if visible is not None:
        params["visible"] = visible
    if locked is not None:
        params["locked"] = locked
    if user_strings is not None:
        params["user_strings"] = user_strings
    if delete_user_strings is not None:
        params["delete_user_strings"] = delete_user_strings
    if clear_user_strings:
        params["clear_user_strings"] = True

    update_keys = {
        "new_name",
        "layer",
        "color",
        "material_index",
        "visible",
        "locked",
        "user_strings",
        "delete_user_strings",
        "clear_user_strings",
    }
    if not any(key in params for key in update_keys):
        raise ValueError(
            "update_object_attributes requires at least one attribute update."
        )

    if params.get("visible") is False and params.get("locked") is True:
        raise ValueError("Object cannot be hidden and locked at the same time.")

    if user_strings is not None:
        for key, value in user_strings.items():
            if key == "":
                raise ValueError("User string keys cannot be empty.")
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                raise ValueError(
                    "User string values must be strings, numbers, booleans, or null."
                )

    return rhino.send_command("update_object_attributes", params)
