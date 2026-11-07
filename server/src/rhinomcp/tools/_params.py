"""Private helpers for building command params (not a tool module: the leading
underscore keeps it out of tool auto-discovery)."""

from typing import Any, Dict


def given(**fields: Any) -> Dict[str, Any]:
    """The fields that were passed, without the ones left at None."""
    return {name: value for name, value in fields.items() if value is not None}
