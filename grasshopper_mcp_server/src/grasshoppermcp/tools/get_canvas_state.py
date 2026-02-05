"""Get the current state of the Grasshopper canvas."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any


@mcp.tool()
def get_canvas_state(ctx: Context) -> Dict[str, Any]:
    """
    Get the current state of the Grasshopper canvas including all components and connections.

    This provides a comprehensive snapshot of the entire definition.

    Returns:
    - component_count: Total number of components
    - connection_count: Total number of connections
    - components: List of all components with their:
        - instance_id: GUID
        - name: Component name
        - nickname: Nickname
        - category: Component category
        - position: [x, y] position
        - inputs: Input parameter info
        - outputs: Output parameter info
        - runtime_message_level: Error/Warning/Blank
    - connections: List of all connections with:
        - source_id: Source component GUID
        - source_output: Output index
        - target_id: Target component GUID
        - target_input: Input index
    - groups: List of groups with their objects

    Example:
        state = get_canvas_state()
        print(f"Canvas has {state['component_count']} components")
        for comp in state['components']:
            print(f"  {comp['nickname']}: {comp['name']}")
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command("get_canvas_state", {})
    except Exception as e:
        logger.error(f"Error getting canvas state: {str(e)}")
        return {"success": False, "message": str(e)}
