"""Guarded subset of production MCP tools, preserving their public definitions."""

import asyncio
import json
import os
from pathlib import Path
import time
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import MCPError
from mcp.types import CallToolResult, ListToolsResult, TextContent
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
    "create_planar_region",
    "get_modeling_guidance",
)


class Gateway:
    def __init__(
        self,
        document,
        marker,
        budget,
        log,
        production=None,
        guard=None,
        description_suffix="",
        tool_names=None,
    ):
        if budget < 1:
            raise ValueError("Positive call budget required")
        self.document, self.marker, self.budget = document, marker, budget
        self.log = Path(log)
        self.production = production or rhinomcp.mcp
        self.guard = guard or assert_document
        self.description_suffix = description_suffix
        self.tool_names = tuple(tool_names) if tool_names is not None else TOOLS
        if (
            self.tool_names[: len(TOOLS)] != TOOLS
            or len(set(self.tool_names)) != len(self.tool_names)
            or set(self.tool_names)
            & {
                "run_command",
                "execute_rhinocommon_csharp_code",
                "execute_rhinoscript_python_code",
            }
        ):
            raise ValueError("Invalid reviewed tool extension")
        self.calls = 0
        self.lock = asyncio.Lock()

    async def definitions(self):
        available = {t.name: t for t in await self.production.list_tools()}
        result = [available[name].model_copy(deep=True) for name in self.tool_names]
        if self.description_suffix:
            tool = next(t for t in result if t.name == "create_object")
            if self.description_suffix.strip() in (tool.description or ""):
                raise ValueError(
                    "Candidate guidance is already present in production; restore the recorded baseline before replay"
                )
            tool.description = (tool.description or "") + self.description_suffix
        return result

    async def call(self, name, arguments):
        # Serialize document guard + operation, including concurrent client calls.
        async with self.lock:
            self.calls += 1
            event = {"attempt": self.calls, "tool": name, "arguments": arguments}
            started = time.monotonic()
            try:
                if name not in self.tool_names:
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
        description_suffix=Path(os.environ["EXPERIMENT_DESCRIPTION_FILE"]).read_text()
        if os.environ.get("EXPERIMENT_DESCRIPTION_FILE")
        else "",
        tool_names=json.loads(os.environ["EXPERIMENT_TOOL_NAMES"])
        if os.environ.get("EXPERIMENT_TOOL_NAMES")
        else None,
    )

    async def list_tools(_context, _params):
        return ListToolsResult(tools=await gateway.definitions())

    async def call_tool(_context, params):
        # The production server performs its normal argument validation; the
        # low-level server adds no second layer, so malformed calls still consume
        # budget and are recorded by our observer. SDK 2.x no longer turns handler
        # exceptions into tool errors, so every gateway rejection or production
        # failure is returned here as an is_error result carrying its text, as
        # the recorded 1.x runs did.
        try:
            return await gateway.call(params.name, params.arguments or {})
        except MCPError:
            raise
        except Exception as error:
            return CallToolResult(
                is_error=True,
                content=[TextContent(type="text", text=str(error))],
            )

    server = Server(
        name="RhinoMCP workflow pilot",
        instructions=rhinomcp.mcp.instructions,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
