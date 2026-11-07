from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, Dict, Optional


@mcp.tool(
    title="Select objects",
    annotations=ToolAnnotations(
        title="Select objects",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def select_objects(
    ctx: Context,
    filters: Optional[Dict[str, Any]] = None,
    filters_type: str = "and",
) -> str:
    """
    Select objects in the Rhino document. Replaces the current selection.

    Parameters:
    - filters: A dictionary containing the filters. The filters parameter is necessary, unless it's empty, in which case all objects will be selected.
    - filters_type: The type of the filters, it's "and" or "or", default is "and"

    Filter semantics:
    - With filters_type="and", an object matches when every filter key matches.
    - With filters_type="or", an object matches when any filter key matches.
    - Name and custom-attribute string matches are exact (case-sensitive).

    Keys:
    - name: list of object names, e.g. ["Box1", "Box2"]
    - color: single RGB triplet, e.g. [255, 0, 0]
    - ids: list of object ids; an id not in the document is refused with not_found
    - layer: full layer path, e.g. "Furniture::Chairs"; an unknown layer is refused
      with not_found
    - type: one type name or a list, e.g. "CURVE" or ["BREP", "EXTRUSION"]
      (POINT, LINE, POLYLINE, CIRCLE, ARC, CURVE, SURFACE, BREP, EXTRUSION, ...)
    - hidden: true matches hidden objects, false matches visible ones
    - locked: true matches locked objects, false matches unlocked ones
    - any other key is treated as a user custom attribute and the value is a list
      of strings, so the names above cannot be used as custom attribute keys.

    Hidden and locked objects (or objects on hidden or locked layers) are only
    considered when hidden=true or locked=true is given. Rhino cannot select an
    object that is itself hidden or locked, so those count as matched but not
    selected; show or unlock them first.

    Example:
    filters = {
        "layer": "Walls",
        "type": "EXTRUSION",
        "name": ["object_name1", "object_name2"],
        "category": ["custom_attribute_value"]
    },
    filters_type = "and"


    Returns:
    How many objects were selected, and how many matched but could not be selected.
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()
        command_params = {"filters": filters or {}, "filters_type": filters_type}

        result = rhino.send_command("select_objects", command_params)

        count = result["count"]
        text = f"Selected {count} objects"
        matched = result.get("matched", count)
        if matched > count:
            text += (
                f" ({matched} matched; {matched - count} hidden or locked and Rhino "
                "cannot select them: show or unlock them first)"
            )
        return text
    except Exception as e:
        logger.error(f"Error selecting objects: {str(e)}")
        raise
