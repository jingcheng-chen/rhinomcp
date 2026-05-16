from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, Dict, List, Optional


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def analyze_objects(
    ctx: Context,
    id: Optional[str] = None,
    name: Optional[str] = None,
    object_ids: Optional[List[str]] = None,
    selected: bool = False,
) -> Dict[str, Any]:
    """
    Analyze object validity and common geometry measurements.

    Provide exactly one target selector:
    - id: Analyze one object by GUID
    - name: Analyze one object by name
    - object_ids: Analyze multiple objects by GUID
    - selected: Analyze the current Rhino selection

    Returns:
    - object_count: Number of analyzed objects
    - analyses: Per-object reports with validity, bounding box dimensions,
      and type-specific measurements such as length, area, volume, centroid,
      closed/solid flags, and Brep/Mesh counts where available.
    """
    selectors = [
        id is not None,
        name is not None,
        object_ids is not None,
        selected,
    ]
    if sum(1 for selector in selectors if selector) != 1:
        raise ValueError(
            "analyze_objects requires exactly one of id, name, object_ids, or selected=true."
        )
    if object_ids is not None and len(object_ids) == 0:
        raise ValueError("analyze_objects object_ids must contain at least one id.")

    rhino = get_rhino_connection()

    params: Dict[str, Any] = {}
    if id is not None:
        params["id"] = id
    elif name is not None:
        params["name"] = name
    elif object_ids is not None:
        params["object_ids"] = object_ids
    else:
        params["selected"] = True

    return rhino.send_command("analyze_objects", params)
