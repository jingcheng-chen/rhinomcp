from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger


@mcp.tool()
def undo(ctx: Context, steps: int = 1) -> str:
    """
    Undo the last operation(s) in the Rhino document.

    Parameters:
    - steps: Number of operations to undo (default: 1)

    Returns:
    A message indicating how many operations were undone.
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("undo", {"steps": steps})
        return result["message"]
    except Exception as e:
        logger.error(f"Error undoing: {str(e)}")
        return f"Error undoing: {str(e)}"


@mcp.tool()
def redo(ctx: Context, steps: int = 1) -> str:
    """
    Redo the last undone operation(s) in the Rhino document.

    Parameters:
    - steps: Number of operations to redo (default: 1)

    Returns:
    A message indicating how many operations were redone.
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("redo", {"steps": steps})
        return result["message"]
    except Exception as e:
        logger.error(f"Error redoing: {str(e)}")
        return f"Error redoing: {str(e)}"
