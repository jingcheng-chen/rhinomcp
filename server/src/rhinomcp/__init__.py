"""Rhino integration through the Model Context Protocol."""

import importlib
import pkgutil
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path

try:
    __version__ = _pkg_version("rhinomcp")
except PackageNotFoundError:
    # Editable/source checkouts without metadata fall back to "0+unknown" rather
    # than a hardcoded value that would silently drift from pyproject.toml.
    __version__ = "0+unknown"

# Expose key classes and functions for easier imports.
# IMPORTANT: server (mcp, get_rhino_connection, logger) must be imported BEFORE
# tool auto-discovery below — tool modules import from this package's namespace.
# These imports look "unused" to ruff but they form the package's public API.
from .static.rhinoscriptsyntax import rhinoscriptsyntax_json as rhinoscriptsyntax_json
from .server import (  # noqa: F401  (public re-exports)
    RhinoConnection,
    get_rhino_connection,
    mcp,
    logger,
)

# Prompts
from .prompts.assert_general_strategy import (  # noqa: F401  (public re-exports)
    asset_general_strategy,
    rhinoscript_workflow,
)

# Auto-discover and register tool modules.
# Each module under tools/ uses @mcp.tool() to register on import. To add a new
# tool, drop a file `tools/<command>.py` — no edits to this file required.
# Modules whose name starts with "_" are skipped (treat them as private helpers).
#
# We also re-export each module's public callables at the package level so that
# `from rhinomcp import create_object` keeps working — preserving the pre-3.x
# package API without re-introducing the manual import list.
def _discover_and_register_tools() -> None:
    tools_dir = Path(__file__).parent / "tools"
    package_globals = globals()
    for info in pkgutil.iter_modules([str(tools_dir)]):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.tools.{info.name}")
        for attr in dir(mod):
            if attr.startswith("_"):
                continue
            value = getattr(mod, attr)
            if callable(value) and getattr(value, "__module__", None) == mod.__name__:
                package_globals[attr] = value


_discover_and_register_tools()
del _discover_and_register_tools
