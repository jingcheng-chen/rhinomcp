"""Guarded subset of production MCP tools, preserving their public definitions."""

import asyncio
import json
import os
from pathlib import Path
import time
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
import rhinomcp
from experiments.bridge import assert_document

# One suite-wide interface, not a task-specific recipe. Arbitrary execution and
# filesystem/desktop tools are outside this pilot's permissions.
TOOLS = (
    "create_object",
    "modify_object",
    "delete_object",
    "analyze_objects",
    "get_object_info",
    "get_objects",
    "extrude_curve",
    "loft",
    "sweep1",
    "boolean_difference",
    "boolean_union",
    "boolean_intersection",
)


class Gateway:
    def __init__(self, document, marker, budget, log, production=None, guard=None):
        if budget < 1:
            raise ValueError("Positive call budget required")
        self.document, self.marker, self.budget = document, marker, budget
        self.log = Path(log)
        self.production = production or rhinomcp.mcp
        self.guard = guard or assert_document
        self.calls = 0
        self.lock = asyncio.Lock()

    async def definitions(self):
        available = {t.name: t for t in await self.production.list_tools()}
        return [available[name] for name in TOOLS]

    async def call(self, name, arguments):
        # Serialize document guard + operation, including concurrent client calls.
        async with self.lock:
            self.calls += 1
            event = {"attempt": self.calls, "tool": name, "arguments": arguments}
            started = time.monotonic()
            try:
                if name not in TOOLS:
                    raise ValueError("Tool outside pilot scope")
                if self.calls > self.budget:
                    raise RuntimeError("Task tool-call budget exhausted")
                self.guard(self.document, self.marker)
                result = await self.production.call_tool(name, arguments)
                event["status"] = "returned"
                return result
            except Exception as error:
                event.update(status="error", error=str(error))
                raise
            finally:
                event["elapsed_seconds"] = time.monotonic() - started
                with self.log.open("a") as stream:
                    stream.write(json.dumps(event) + "\n")


async def main():
    gateway = Gateway(
        int(os.environ["EXPERIMENT_DOCUMENT"]),
        os.environ["EXPERIMENT_MARKER"],
        int(os.environ["EXPERIMENT_MAX_CALLS"]),
        os.environ["EXPERIMENT_CALL_LOG"],
    )
    server = Server("RhinoMCP workflow pilot")
    server.list_tools()(gateway.definitions)
    # FastMCP performs its normal argument validation. Disabling the extra layer
    # also means malformed calls consume budget and are recorded by our observer.
    server.call_tool(validate_input=False)(gateway.call)
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
