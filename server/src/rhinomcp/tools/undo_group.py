from typing import Any, Dict, Optional

from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations

from rhinomcp.server import get_rhino_connection, mcp
from rhinomcp.tools._params import given


@mcp.tool(
    title="Begin undo group",
    annotations=ToolAnnotations(
        title="Begin undo group",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def begin_undo_group(
    ctx: Context,
    name: str,
    idle_timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Make the next edits one undo step. Rhino normally records one undo step per
    tool call; inside a group every change to the document lands in one step,
    so a single Undo takes the whole change back.

    Use it around a multi-step change the user would undo as a whole, for
    example one object built from several create, boolean and modify calls.
    Call end_undo_group when the change is done. Groups do not nest.

    While a group is open:
    - undo and redo are refused, since the group's step is still being
      recorded; correct a mistake with modify_object or delete_object instead.
    - edits the user makes in Rhino, and edits from other MCP clients, join
      the group.

    The plugin also ends the group when this client disconnects, when no
    command arrives for idle_timeout_seconds, and when the document is closed
    or another document becomes active.

    Parameters:
    - name: short name for the change, e.g. "Build chair frame". Rhino lists
      the step as "MCP: <name>".
    - idle_timeout_seconds: end the group after this many seconds without any
      command (default 120, at most 3600).

    Returns name, undo_description, document_name, idle_timeout_seconds and a
    message. Requires plugin 0.6.0.
    """
    params = given(name=name, idle_timeout_seconds=idle_timeout_seconds)
    return get_rhino_connection().send_command("begin_undo_group", params)


@mcp.tool(
    title="End undo group",
    annotations=ToolAnnotations(
        title="End undo group",
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
    ),
)
def end_undo_group(ctx: Context) -> Dict[str, Any]:
    """
    End the undo group begun with begin_undo_group. Its changes become one
    undo step, and later edits get their own steps again.

    Returns ended=true with the group's name, command_count and
    duration_seconds. With no group open it returns ended=false instead of
    failing; last_group then says why the previous group already ended (for
    example idle_timeout), and edits made after that have their own undo steps.
    Requires plugin 0.6.0.
    """
    return get_rhino_connection().send_command("end_undo_group", {})
