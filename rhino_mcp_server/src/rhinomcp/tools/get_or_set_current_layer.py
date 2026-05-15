from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger

@mcp.tool()
def get_or_set_current_layer(
    ctx: Context,
    guid: str = None,
    name: str = None
) -> str:
    """
    Get or set the current layer in the Rhino document.
    If name is provided, it will try to set the current layer to the layer with the given name.
    If guid is provided, it will try to set the current layer to the layer with the given guid.
    If neither is provided, it will return the current layer.
    
    Parameters:
    - name: The name of the layer to set the current layer to.
    - guid: The guid of the layer to set the current layer to.
    
    Returns:
    A message indicating the current layer.
    
    Examples of params:
    - name: "Layer 1"
    - guid: "00000000-0000-0000-0000-000000000000"
    """
    try:
        # Get the global connection
        rhino = get_rhino_connection()

        command_params = {}

        if name is not None:
            command_params["name"] = name
        if guid is not None:
            command_params["guid"] = guid

        # Create the layer
        result = rhino.send_command("get_or_set_current_layer", command_params)  
        
        return f"Current layer: {result['name']}"
    except Exception as e:
        logger.error(f"Error getting or setting current layer: {str(e)}")
        return f"Error getting or setting current layer: {str(e)}"
 