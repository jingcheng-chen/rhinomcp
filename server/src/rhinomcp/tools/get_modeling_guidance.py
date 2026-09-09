"""Local documentation access; no Rhino command or document mutation."""

from typing import Any, Dict, Literal

from mcp.types import ToolAnnotations

from rhinomcp.guidance import modeling_guidance
from rhinomcp.server import mcp


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def get_modeling_guidance(
    topic: Literal[
        "overview",
        "transforms",
        "planar_regions",
        "organization",
        "verification",
        "recovery",
    ] = "overview",
) -> Dict[str, Any]:
    """Read the versioned Rhino modeling guide bundled with this server.

    Consult transforms for anchors and world-origin rotation, planar_regions for
    faces with holes, organization for layer assignment, verification for checking
    results, or recovery after uncertain edits. overview lists the workflow and
    topics. Works without a Rhino connection; does not change documents.
    """
    return modeling_guidance(topic)


@mcp.resource("rhinomcp://guidance/{topic}", mime_type="text/markdown")
def modeling_guidance_resource(topic: str) -> str:
    """Read the same bundled guide through an MCP resource."""
    return modeling_guidance(topic)["content"]
