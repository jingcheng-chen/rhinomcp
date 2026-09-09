"""Screenshot integration gateway with fixed Join and read-only review enforcement."""

import os
from experiments import visual_mcp as visual
from experiments.cushion_body_mcp import join_script
from rhinomcp.server import get_rhino_connection

visual.COMMANDS = visual.COMMANDS | {"get_object_attributes"}
COMMANDS = visual.COMMANDS
mcp = visual.mcp


@mcp.tool()
def join_surfaces(ids: list[str]) -> dict:
    """Join 2..12 surface IDs through native Rhino Join, with no raw macro input.
    Inspect get_objects for the result ID; then set its name and layer. Requires
    coincident edges. Closed geometry is checked independently by the supervisor.
    """
    visual.guard()
    if os.environ.get("EXPERIMENT_READ_ONLY") == "1":
        raise RuntimeError("Review gateway cannot join geometry")
    params = {"command": join_script(ids), "echo": False}
    try:
        result = get_rhino_connection().send_command("run_command", params)
    except Exception as exc:
        visual.record({"command": "run_command", "params": params, "error": str(exc)})
        raise
    visual.record({"command": "run_command", "params": params, "result": result})
    return result


if __name__ == "__main__":
    mcp.run()
