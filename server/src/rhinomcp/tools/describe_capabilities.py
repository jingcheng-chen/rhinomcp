from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from rhinomcp.server import get_rhino_connection, mcp
from typing import Any, Dict


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def describe_capabilities(ctx: Context) -> Dict[str, Any]:
    """
    Describe what this MCP server itself can do.

    Unlike get_commands, which lists Rhino's own application commands (Box,
    Circle, ...) for use with run_command, this lists the MCP command surface:
    every command the server handles and whether it is read-only, so you can
    discover what is callable here instead of guessing a name.

    Returns:
    - version: the plugin version
    - command_count: how many commands the server handles
    - commands: a list of {name, read_only}, sorted by name
    - perception: the opt-in envelope flags (include_delta, include_health) and
      what each attaches to a mutating command's result
    """
    rhino = get_rhino_connection()
    return rhino.send_command("describe_capabilities", {})
