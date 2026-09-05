"""Narrow MCP gateway: no code execution, file access, reset, or evaluator tools."""

import os
from mcp.server.fastmcp import FastMCP
from rhinomcp.tools.create_object import create_object as original_create
from rhinomcp.tools.analyze_objects import analyze_objects as original_analyze
from rhinomcp.tools.modify_object import modify_object as original_modify
from rhinomcp.tools.advanced_geometry import extrude_curve as original_extrude
from rhinomcp.tools.delete_object import delete_object as original_delete
from experiments.bridge import assert_document

mcp = FastMCP("RhinoMCP experiment")
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

    POLYLINE params: points, a list of XYZ triples. Repeat the first point to close.

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
def delete_object(id: str):
    """Delete one construction object by ID in the dedicated experiment document."""
    guard()
    return original_delete(None, id=id)


@mcp.tool()
def analyze_objects(object_ids: list[str]):
    """Inspect validity, bounding dimensions, and volume for created objects."""
    guard()
    return original_analyze(None, object_ids=object_ids)


if __name__ == "__main__":
    mcp.run()
