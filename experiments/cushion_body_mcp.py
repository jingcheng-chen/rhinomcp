"""Body-task gateway: existing creation tools plus a fixed native Join recipe."""

from uuid import UUID
from rhinomcp.server import get_rhino_connection
from experiments.layer_modeler_mcp import mcp, COMMANDS  # noqa: F401
from experiments.visual_mcp import guard, record


def join_script(ids):
    if not 2 <= len(ids) <= 12:
        raise ValueError("Join requires 2..12 distinct object IDs")
    values = [str(UUID(value)) for value in ids]
    if len(set(values)) != len(values) or any(UUID(v).int == 0 for v in values):
        raise ValueError("Join requires distinct nonzero object IDs")
    return (
        "_SelNone " + " ".join("_SelID " + v for v in values) + " _Join _Enter _SelNone"
    )


@mcp.tool()
def join_surfaces(ids: list[str]) -> dict:
    """Join 2..12 existing surfaces using Rhino's native Join command. Returns
    command output; inspect get_objects afterward for the new ID, then set its
    final name/layer. Coincident edges are required. No arbitrary command strings.
    """
    guard()
    params = {"command": join_script(ids), "echo": False}
    try:
        result = get_rhino_connection().send_command("run_command", params)
    except Exception as exc:
        record({"command": "run_command", "params": params, "error": str(exc)})
        raise
    record({"command": "run_command", "params": params, "result": result})
    return result


if __name__ == "__main__":
    mcp.run()
