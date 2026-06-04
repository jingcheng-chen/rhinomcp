from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict, Optional


@mcp.tool()
def select_objects(
    ctx: Context,
    filters: Optional[Dict[str, List[Any]]] = None,
    filters_type: str = "and",
) -> str:
    """
    Select objects in the Rhino document.
    
    Parameters:
    - filters: A dictionary containing the filters. The filters parameter is necessary, unless it's empty, in which case all objects will be selected.
    - filters_type: The type of the filters, it's "and" or "or", default is "and"

    Note:
    Name and custom attribute filter values are lists of strings (even if there's only one value).
    `color` is a single RGB triplet (not a list of triplets).

    Filter semantics:
    - With filters_type="and", an object matches when every filter key matches at least one
      of that key's listed values.
    - With filters_type="or", an object matches when any filter key matches any listed value.
    - Name and custom-attribute string matches are exact (case-sensitive).

    Keys:
    - name: list of object names, e.g. ["Box1", "Box2"]
    - color: single RGB triplet, e.g. [255, 0, 0]
    - any other key is treated as a user custom attribute and the value is a list of strings.

    Example:
    filters = {
        "name": ["object_name1", "object_name2"],
        "category": ["custom_attribute_value"]
    },
    filters_type = "or"
    

    Returns:
    A number indicating the number of objects that have been selected.
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()
        command_params = {
            "filters": filters or {},
            "filters_type": filters_type
        }

        result = rhino.send_command("select_objects", command_params)
          
        return f"Selected {result['count']} objects"
    except Exception as e:
        logger.error(f"Error selecting objects: {str(e)}")
        return f"Error selecting objects: {str(e)}"

