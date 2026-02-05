"""Grasshopper integration through the Model Context Protocol."""

__version__ = "0.1.0"

from .server import mcp, get_grasshopper_connection, logger

# Prompts
from .prompts.gh_strategy import gh_general_strategy, gh_workflow

# Document tools
from .tools.get_document_info import get_gh_document_info

# Component tools
from .tools.list_components import list_components
from .tools.add_component import add_component
from .tools.delete_component import delete_component
from .tools.get_component_info import get_component_info

# Connection tools
from .tools.connect_components import connect_components
from .tools.disconnect_components import disconnect_components

# Parameter tools
from .tools.set_parameter_value import set_parameter_value
from .tools.get_parameter_value import get_parameter_value

# Solution tools
from .tools.run_solution import run_solution
from .tools.expire_solution import expire_solution
from .tools.bake_component import bake_component

# Canvas tools
from .tools.get_canvas_state import get_canvas_state


def main():
    """Run the MCP server."""
    mcp.run()
