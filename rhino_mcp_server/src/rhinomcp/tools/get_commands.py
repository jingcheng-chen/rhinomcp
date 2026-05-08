from mcp.server.fastmcp import Context
import json
from rhinomcp import get_rhino_connection, mcp, logger


@mcp.tool()
def get_commands(ctx: Context, filter: str = "", loaded_only: bool = True) -> str:
    """
    List Rhino command names available in the current session.

    Use this together with `run_command` to discover what is invokable before guessing
    a command name. Filter is a case-insensitive substring match — pass "boolean" to
    find every boolean-related command, "view" for view commands, and so on.

    Parameters:
    - filter: Optional case-insensitive substring. Empty string returns all commands.
    - loaded_only: If True (default), only commands from currently loaded plugins are
                   returned. Set False to also include commands from unloaded plugins.

    Returns a JSON object: {"count": N, "commands": ["Box", "Circle", ...]}
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command(
            "get_commands", {"filter": filter, "loaded_only": loaded_only}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing Rhino commands: {str(e)}")
        return f"Error listing Rhino commands: {str(e)}"
