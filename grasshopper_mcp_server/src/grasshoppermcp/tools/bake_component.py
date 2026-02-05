"""Bake a component's geometry to the Rhino document."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any, Optional, List


@mcp.tool()
def bake_component(
    ctx: Context,
    instance_id: Optional[str] = None,
    nickname: Optional[str] = None,
    output_index: int = 0,
    layer_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Bake a component's geometry output to the Rhino document.

    Parameters:
    - instance_id: GUID of the component to bake
    - nickname: Nickname of the component to bake (alternative to instance_id)
    - output_index: Index of the output parameter to bake (default: 0)
    - layer_name: Name of the layer to bake to (creates if doesn't exist)

    At least one of instance_id or nickname must be provided.

    Returns:
    - baked_count: Number of objects baked
    - object_ids: List of GUIDs of the baked Rhino objects
    - layer: Name of the layer objects were baked to
    - message: Confirmation message

    Example:
        # Bake a circle to Rhino
        result = bake_component(nickname="MyCircle")
        print(f"Baked {result['baked_count']} objects")

        # Bake to a specific layer
        bake_component(nickname="MyExtrusion", layer_name="Grasshopper Bake")
    """
    try:
        if not instance_id and not nickname:
            return {"success": False, "message": "Either instance_id or nickname is required"}

        gh = get_grasshopper_connection()
        params = {"output_index": output_index}
        if instance_id:
            params["instance_id"] = instance_id
        if nickname:
            params["nickname"] = nickname
        if layer_name:
            params["layer_name"] = layer_name

        result = gh.send_command("bake_component", params)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error baking component: {str(e)}")
        return {"success": False, "message": str(e)}
