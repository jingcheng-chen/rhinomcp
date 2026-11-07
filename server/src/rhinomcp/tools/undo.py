from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp, logger


@mcp.tool(
    title="Undo",
    annotations=ToolAnnotations(
        title="Undo",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
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
        raise


@mcp.tool(
    title="Redo",
    annotations=ToolAnnotations(
        title="Redo",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
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
        raise
