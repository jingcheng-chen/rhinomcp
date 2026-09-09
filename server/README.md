# RhinoMCP - Rhino Model Context Protocol Integration

RhinoMCP connects Rhino to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with and control Rhino. This integration enables prompt assisted 3D modeling in Rhino 3D.

Please visit Github for complete information:

[Github](https://github.com/jingcheng-chen/rhinomcp)

## Bundled modeling guidance

RhinoMCP ships versioned modeling knowledge with the Python server. No experiment
checkout, local memory folder or separate skill installation is required.

- Call `get_modeling_guidance(topic="overview")` to start. Other topics are
  `transforms`, `planar_regions`, `organization`, `verification` and `recovery`.
- Clients supporting MCP resources can read `rhinomcp://guidance/{topic}`.
- The `asset_general_strategy` MCP prompt uses the same packaged overview.
- Server instructions advertise the guide, and individual tool descriptions retain
  essential behavior such as units and rotation pivots. Client support determines
  how instructions, prompts and resources appear; their presence does not guarantee
  an agent reads them.

The canonical Markdown files are packaged under `rhinomcp/guides`. Guide responses
include both the guide revision and installed package version. Any future optional
client skill should derive its content from these files, not maintain another copy.
The contributor experiment harness remains separate from normal modeling guidance.

This implementation uses MCP Python SDK 2.x (`mcp>=2.0.0,<3`); SDK 1.x is no
longer supported. New guidance ships when this server version is released;
local builds are not a PyPI publication. Restart an existing MCP server connection
after upgrading so its tool descriptions and instructions refresh.
