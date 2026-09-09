"""Narrow MCP gateway: no code execution, file access, reset, or evaluator tools."""

import os
from typing import Literal
from mcp.server.mcpserver import MCPServer
from rhinomcp.tools.create_object import create_object as original_create
from rhinomcp.tools.analyze_objects import analyze_objects as original_analyze
from rhinomcp.tools.modify_object import modify_object as original_modify
from rhinomcp.tools.advanced_geometry import extrude_curve as original_extrude
from rhinomcp.tools.advanced_geometry import sweep1 as original_sweep
from rhinomcp.tools.delete_object import delete_object as original_delete
from rhinomcp.tools.boolean_operations import boolean_difference as original_difference
from experiments.bridge import assert_document

mcp = MCPServer("RhinoMCP experiment")
calls = 0


def guard():
    global calls
    calls += 1
    if calls > int(os.environ["EXPERIMENT_MAX_CALLS"]):
        raise RuntimeError("Task tool-call budget exhausted")
    assert_document(
        int(os.environ["EXPERIMENT_DOCUMENT"]), os.environ["EXPERIMENT_MARKER"]
    )


@mcp.tool()
def create_object(type: str, params: dict, translation: list[float] | None = None):
    """Create a primitive. BOX params: width (X), length (Y), height (Z).

    ARC params: center (XYZ), radius and angle (degrees), from +X in the XY plane.
    POLYLINE params: points, a list of XYZ triples. Repeat the first point to close.
    CYLINDER params: radius, height, cap (true for a solid). Its base is at world
    origin and height runs along +Z; translation offsets it. BOX is centered at origin.

    Primitives use the plugin's default placement; translation offsets the result.
    The returned bounding box shows the actual extent. Units are millimeters.
    """
    guard()
    return original_create(None, type=type, params=params, translation=translation)


@mcp.tool()
def translate_object(id: str, translation: list[float]):
    """Translate an existing object by a world XYZ vector in millimeters."""
    guard()
    return original_modify(None, id=id, translation=translation)


@mcp.tool()
def rotate_object(id: str, rotation: list[float]):
    """Rotate about the CURRENT WORLD BOUNDING-BOX CENTER, using XYZ radians.

    This is not rotation about world origin or volume centroid. For a different
    pivot compensate the final translation, or construct an already posed profile.
    """
    guard()
    return original_modify(None, id=id, rotation=rotation)


@mcp.tool()
def extrude_curve(curve_id: str, direction: list[float], cap: bool = True):
    """Extrude a profile by a world XYZ vector. Cap a closed planar profile to
    create a solid. The original curve remains; delete it separately if unwanted.
    """
    guard()
    result = original_extrude(None, curve_id=curve_id, direction=direction, cap=cap)
    if not result.get("success"):
        raise RuntimeError(result.get("message", "Extrusion failed"))
    return result


@mcp.tool()
def sweep1(rail_id: str, profile_ids: list[str], cap_planar_ends: bool = False):
    """Sweep profiles along one rail using RoadlikeTop framing. Optional planar
    end caps require every output to be a valid solid or fail before insertion.
    Rail and profile curves remain; delete construction geometry separately.
    """
    guard()
    result = original_sweep(None, rail_id, profile_ids, cap_planar_ends=cap_planar_ends)
    if not result.get("success"):
        raise RuntimeError(result.get("message", "Sweep failed"))
    return result


@mcp.tool()
def delete_object(id: str):
    """Delete one construction object by ID in the dedicated experiment document."""
    guard()
    return original_delete(None, id=id)


@mcp.tool()
def boolean_difference(base_id: str, subtract_ids: list[str]):
    """Subtract closed-solid cutters from a base solid. On success deletes sources
    and returns the resulting object IDs in the message. A cutter extending beyond
    both block faces can produce a through-hole. Inspect the result before claiming success.
    """
    guard()
    return original_difference(
        None, base_id=base_id, subtract_ids=subtract_ids, delete_sources=True
    )


@mcp.tool()
def analyze_objects(object_ids: list[str]):
    """Inspect validity, bounding dimensions, and volume for created objects."""
    guard()
    return original_analyze(None, object_ids=object_ids)


@mcp.tool()
def get_reference_image(view: Literal["top", "front", "right"]):
    """Read one calibrated reference image. No candidate or hidden model access."""
    guard()
    from experiments.references import reference_image

    return reference_image(view)


if __name__ == "__main__":
    mcp.run()
