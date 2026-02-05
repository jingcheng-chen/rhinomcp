"""Rhino integration through the Model Context Protocol."""

__version__ = "0.1.0"

# Expose key classes and functions for easier imports
from .static.rhinoscriptsyntax import rhinoscriptsyntax_json
from .server import RhinoConnection, get_rhino_connection, mcp, logger

# Prompts
from .prompts.assert_general_strategy import asset_general_strategy, rhinoscript_workflow

# Object tools
from .tools.create_object import create_object
from .tools.create_objects import create_objects
from .tools.delete_object import delete_object
from .tools.get_document_summary import get_document_summary
from .tools.get_objects import get_objects
from .tools.get_object_info import get_object_info
from .tools.get_selected_objects_info import get_selected_objects_info
from .tools.modify_object import modify_object
from .tools.modify_objects import modify_objects
from .tools.select_objects import select_objects

# Layer tools
from .tools.create_layer import create_layer
from .tools.get_or_set_current_layer import get_or_set_current_layer
from .tools.delete_layer import delete_layer

# RhinoScript execution and documentation tools
from .tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code
from .tools.execute_rhinocommon_csharp_code import execute_rhinocommon_csharp_code
from .tools.rhinoscript_docs import (
    search_rhinoscript_functions,
    get_rhinoscript_docs,
    list_rhinoscript_modules,
    get_module_functions,
)

# Utility tools
from .tools.undo import undo, redo
from .tools.boolean_operations import boolean_union, boolean_difference, boolean_intersection
from .tools.capture_viewport import capture_viewport

# Advanced geometry tools
from .tools.advanced_geometry import loft, extrude_curve, sweep1, offset_curve, pipe