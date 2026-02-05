"""
Common patterns and utilities for MCP tools.

Provides decorators and helper functions for building consistent tools.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


def validate_params(
    required: Optional[List[str]] = None,
    types: Optional[Dict[str, type]] = None
) -> Callable:
    """
    Decorator to validate tool parameters.

    Args:
        required: List of required parameter names
        types: Dict mapping parameter names to expected types

    Example:
        ```python
        @mcp.tool()
        @validate_params(required=["curve_id"], types={"radius": (int, float)})
        def create_pipe(ctx, curve_id: str, radius: float):
            ...
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check required parameters
            if required:
                for param in required:
                    if param not in kwargs or kwargs[param] is None:
                        return {"success": False, "message": f"Missing required parameter: {param}"}

            # Check parameter types
            if types:
                for param, expected_type in types.items():
                    if param in kwargs and kwargs[param] is not None:
                        if not isinstance(kwargs[param], expected_type):
                            return {
                                "success": False,
                                "message": f"Parameter '{param}' must be {expected_type.__name__}, got {type(kwargs[param]).__name__}"
                            }

            return func(*args, **kwargs)
        return wrapper
    return decorator


def command_tool(
    get_connection: Callable,
    command_name: str,
    result_key: Optional[str] = None,
    success_message: Optional[str] = None,
    error_prefix: str = "Error"
) -> Callable:
    """
    Decorator factory for simple command-forwarding tools.

    Creates a tool that forwards parameters to a plugin command
    and handles the standard response pattern.

    Args:
        get_connection: Function to get the plugin connection
        command_name: Name of the command to send to plugin
        result_key: Key to extract from result (if any)
        success_message: Message format for success (can include {result})
        error_prefix: Prefix for error messages

    Example:
        ```python
        @mcp.tool()
        @command_tool(get_rhino_connection, "undo", success_message="Undo successful")
        def undo(ctx, count: int = 1):
            return {"count": count}  # Parameters to send
        ```
    """
    def decorator(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                # Get parameters from the wrapped function
                params = func(*args, **kwargs)
                if params is None:
                    params = {}

                # Send command
                connection = get_connection()
                result = connection.send_command(command_name, params)

                # Build response
                response: Dict[str, Any] = {"success": True}

                if result_key and result_key in result:
                    response[result_key] = result[result_key]
                else:
                    response.update(result)

                if success_message:
                    response["message"] = success_message.format(result=result)
                elif "message" in result:
                    response["message"] = result["message"]

                return response

            except Exception as e:
                logger.error(f"{error_prefix}: {str(e)}")
                return {"success": False, "message": f"{error_prefix}: {str(e)}"}
        return wrapper
    return decorator


def safe_tool(error_prefix: str = "Error") -> Callable:
    """
    Decorator to wrap tools in try/except with consistent error handling.

    Args:
        error_prefix: Prefix for error messages

    Example:
        ```python
        @mcp.tool()
        @safe_tool("Failed to create object")
        def create_object(ctx, ...):
            ...
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Dict[str, Any]]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Dict[str, Any]]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{error_prefix}: {str(e)}")
                return {"success": False, "message": f"{error_prefix}: {str(e)}"}
        return wrapper
    return decorator


def format_result_ids(result_ids: List[str], object_type: str = "object") -> str:
    """
    Format a list of result IDs into a human-readable message.

    Args:
        result_ids: List of GUIDs
        object_type: Type of object for the message

    Returns:
        Formatted message string
    """
    count = len(result_ids)
    if count == 0:
        return f"No {object_type}s created"
    elif count == 1:
        return f"Created {object_type}: {result_ids[0]}"
    else:
        return f"Created {count} {object_type}s: {', '.join(result_ids[:3])}{'...' if count > 3 else ''}"


def parse_point(value: Any) -> Optional[List[float]]:
    """
    Parse various point representations into [x, y, z] format.

    Accepts:
    - List/tuple of 2-3 numbers
    - Dict with x, y, z keys
    - None (returns None)

    Returns:
        List of [x, y, z] or None
    """
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        if len(value) == 2:
            return [float(value[0]), float(value[1]), 0.0]
        elif len(value) >= 3:
            return [float(value[0]), float(value[1]), float(value[2])]

    if isinstance(value, dict):
        return [
            float(value.get("x", 0)),
            float(value.get("y", 0)),
            float(value.get("z", 0))
        ]

    return None


def parse_color(value: Any) -> Optional[Dict[str, int]]:
    """
    Parse various color representations into {r, g, b} format.

    Accepts:
    - List/tuple of 3 numbers (RGB 0-255)
    - Dict with r, g, b keys
    - Hex string "#RRGGBB"
    - None (returns None)

    Returns:
        Dict with r, g, b keys or None
    """
    if value is None:
        return None

    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return {
            "r": int(value[0]),
            "g": int(value[1]),
            "b": int(value[2])
        }

    if isinstance(value, dict):
        return {
            "r": int(value.get("r", 0)),
            "g": int(value.get("g", 0)),
            "b": int(value.get("b", 0))
        }

    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        return {
            "r": int(value[1:3], 16),
            "g": int(value[3:5], 16),
            "b": int(value[5:7], 16)
        }

    return None
