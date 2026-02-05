"""
MCP Shared - Common components for RhinoMCP and GrasshopperMCP servers.

This package provides reusable infrastructure for building MCP servers
that communicate with Rhino/Grasshopper plugins via TCP sockets.
"""

__version__ = "0.1.0"

from .connection import PluginConnection, create_connection_manager
from .lifespan import create_lifespan
from .tool_patterns import command_tool, validate_params

__all__ = [
    "PluginConnection",
    "create_connection_manager",
    "create_lifespan",
    "command_tool",
    "validate_params",
]
