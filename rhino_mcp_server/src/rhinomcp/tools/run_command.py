from mcp.server.fastmcp import Context
from rhinomcp import get_rhino_connection, mcp, logger


@mcp.tool()
def run_command(ctx: Context, command: str, echo: bool = False) -> str:
    """
    Execute a Rhino command string and return whatever the command window prints.

    This is the escape hatch for Rhino commands that do not yet have a typed MCP tool.
    Anything you can type into the Rhino command line works here, including aliases and
    macros. Prefix the command name with an underscore to force the English name (e.g.
    "_Box 0,0,0 10,10,10"). Multiple commands can be chained with newlines.

    Pair this with `get_commands` to discover what command names are available before
    invoking. Prefer the typed tools (create_object, boolean_union, etc.) when one
    exists — they are validated and return structured data.

    Parameters:
    - command: Rhino command string to execute, e.g. "_Box 0,0,0 10,10,10".
    - echo: If True, the command is echoed in the Rhino command window as it runs.
            Default False to keep the output focused on diagnostics.

    Returns the captured command-window output as a string. Failed commands are
    prefixed with "Command failed:" so the agent can distinguish failure from
    silent success without parsing JSON.
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("run_command", {"command": command, "echo": echo})
        output = (result.get("output") or "").strip()
        success = bool(result.get("success", False))

        if success:
            return output if output else "Done."
        # Failure: surface the flag explicitly. Output may still be useful diagnostic.
        if output:
            return f"Command failed: {output}"
        return "Command failed: no output captured."
    except Exception as e:
        logger.error(f"Error running Rhino command: {str(e)}")
        return f"Error running Rhino command: {str(e)}"
