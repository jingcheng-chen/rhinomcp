"""Shared helpers for Grasshopper MCP tool wrappers."""

from typing import Any, Dict, List, Union

from rhinomcp.server import get_rhino_connection


JsonValue = Union[float, int, str, bool, List[Any], Dict[str, Any]]


def send_grasshopper_command(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    rhino = get_rhino_connection()
    return rhino.send_command(command, params)
