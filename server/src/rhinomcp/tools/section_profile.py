from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, Dict, List, Optional


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def section_profile(
    ctx: Context,
    id: Optional[str] = None,
    name: Optional[str] = None,
    object_ids: Optional[List[str]] = None,
    selected: bool = False,
    plane: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Cut a plane through objects and measure each cross-section, without creating
    anything in the document.

    Provide exactly one target selector:
    - id: section one object by GUID
    - name: section one object by name
    - object_ids: section multiple objects by GUID
    - selected: section the current Rhino selection

    Provide exactly one cut:
    - plane: a single cut. Either {"axis": "X"|"Y"|"Z", "value": <number>} for an
      axis-aligned world plane, or {"origin": [x, y, z], "normal": [x, y, z]} for
      an arbitrary plane.
    - profile: a stack of parallel cuts for a sectional-area curve, as
      {"axis": "X"|"Y"|"Z", "count": <2..100>, "start": <number?>, "end": <number?>}.
      Without start/end the stack spans the selection's extent along the axis.

    Returns (plane mode):
    - mode "plane", object_count, the resolved cut plane, total_section_area,
      total_loop_count, and per-object profiles. Each loop reports closed,
      perimeter, and, only when it closed, area and centroid. A single cut can
      produce several disjoint loops, so areas are summed per object.

    Returns (profile mode):
    - mode "profile", axis, count, and sections: one {position, total_section_area,
      loop_count} per slice, i.e. the cross-sectional area along the axis.
    """
    selectors = [id is not None, name is not None, object_ids is not None, selected]
    if sum(1 for s in selectors if s) != 1:
        raise ValueError(
            "section_profile requires exactly one of id, name, object_ids, or selected=true."
        )
    if object_ids is not None and len(object_ids) == 0:
        raise ValueError("section_profile object_ids must contain at least one id.")

    if (plane is None) == (profile is None):
        raise ValueError("section_profile requires exactly one of plane or profile.")

    if plane is not None:
        has_axis = "axis" in plane or "value" in plane
        has_origin_normal = "origin" in plane or "normal" in plane
        if has_axis and has_origin_normal:
            raise ValueError(
                "section_profile plane takes either {axis, value} or {origin, normal}, not both."
            )
        if has_axis:
            if "axis" not in plane or "value" not in plane:
                raise ValueError(
                    "section_profile plane {axis, value} requires both axis and value."
                )
            if plane["axis"] not in ("X", "Y", "Z"):
                raise ValueError("section_profile plane axis must be 'X', 'Y', or 'Z'.")
        elif has_origin_normal:
            if "origin" not in plane or "normal" not in plane:
                raise ValueError(
                    "section_profile plane {origin, normal} requires both origin and normal."
                )
        else:
            raise ValueError(
                "section_profile plane requires {axis, value} or {origin, normal}."
            )

    if profile is not None:
        if profile.get("axis") not in ("X", "Y", "Z"):
            raise ValueError("section_profile profile axis must be 'X', 'Y', or 'Z'.")
        count = profile.get("count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 2 or count > 100:
            raise ValueError(
                "section_profile profile count must be an integer in [2, 100]."
            )

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
    if plane is not None:
        params["plane"] = plane
    else:
        params["profile"] = profile

    return rhino.send_command("section_profile", params)
