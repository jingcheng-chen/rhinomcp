"""Run with a clean wheel-installed Python environment, from any directory.

Example: /tmp/clean/bin/python server/verify_guidance_install.py
No Rhino instance is required; the child intentionally connects to unavailable port 1.
"""

import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

import rhinomcp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rhinomcp.guidance import TOPICS, modeling_guidance


async def verify():
    package = Path(rhinomcp.__file__).resolve()
    package.relative_to(Path(sys.prefix).resolve())  # Reject editable/source imports.
    with tempfile.TemporaryDirectory(prefix="rhinomcp-guidance-smoke-") as cwd:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from rhinomcp.server import main; main()"],
            cwd=cwd,
            env={
                **os.environ,
                "PYTHONPATH": "",
                "RHINO_MCP_PORT": "1",
                "RHINO_MCP_TIMEOUT": "1",
            },
        )
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as client:
                init = await client.initialize()
                assert "get_modeling_guidance" in init.instructions
                tools = (await client.list_tools()).tools
                assert "get_modeling_guidance" in {tool.name for tool in tools}
                for topic in TOPICS:
                    result = await client.call_tool(
                        "get_modeling_guidance", {"topic": topic}
                    )
                    assert not result.is_error
                    data = json.loads(result.content[0].text)
                    assert data == modeling_guidance(topic)
                    resource = await client.read_resource(
                        "rhinomcp://guidance/" + topic
                    )
                    assert resource.contents[0].text == data["content"]
                prompt = await client.get_prompt("asset_general_strategy")
                assert prompt.messages[0].content.text == modeling_guidance()["content"]
                bad = await client.call_tool(
                    "get_modeling_guidance", {"topic": "../../etc/passwd"}
                )
                assert bad.is_error
                return {
                    "package": str(package),
                    "tool_count": len(tools),
                    "topics": list(TOPICS),
                    "offline_mcp_interfaces": "pass",
                    "invalid_topic_rejected": True,
                }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(verify())))
