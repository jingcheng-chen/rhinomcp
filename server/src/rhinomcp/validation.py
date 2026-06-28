"""
RhinoMCP Schema Validation

Validates commands and responses against JSON Schema contracts.
Ensures type safety between Python MCP server and C# Rhino plugin.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("RhinoMCPValidation")

# Try to import jsonschema, but make it optional.
# referencing is a hard dependency of jsonschema>=4.18 (we require >=4.20),
# so grouping the imports keeps the "jsonschema is optional" behavior intact.
try:
    import jsonschema
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema not installed. Validation disabled. Install with: pip install jsonschema")


# Path to contracts directory (relative to this file)
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "contracts"

# Cache for loaded schemas
_schema_cache: Dict[str, Any] = {}


def _get_contracts_dir() -> Path:
    """Get the contracts directory path."""
    # Try relative path first
    if CONTRACTS_DIR.exists():
        return CONTRACTS_DIR

    # Try from project root
    project_root = Path(__file__).parent
    for _ in range(5):  # Walk up to 5 levels
        contracts = project_root / "contracts"
        if contracts.exists():
            return contracts
        project_root = project_root.parent

    raise FileNotFoundError("Could not find contracts directory")


def _load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and cache a JSON schema."""
    if schema_path in _schema_cache:
        return _schema_cache[schema_path]

    contracts_dir = _get_contracts_dir()
    full_path = contracts_dir / schema_path

    if not full_path.exists():
        raise FileNotFoundError(f"Schema not found: {full_path}")

    with open(full_path, "r") as f:
        schema = json.load(f)

    _schema_cache[schema_path] = schema
    return schema


# Cache for the shared $ref registry
_registry: Optional["Registry"] = None


def _get_registry() -> Optional["Registry"]:
    """Build (once) the referencing.Registry for cross-file $ref resolution.

    Refs resolve in the schemas' own relative-URI space (bare `$id`s like
    "create_object.json"), no file:// URIs involved. Every contract schema is
    registered under its filename so cross-file refs resolve from memory:
      - same-directory refs like "object_info.json"
        (used by responses/get_objects_result.json),
      - "common/definitions.json", the form a "../common/definitions.json"
        ref collapses to when resolved against a bare `$id`,
      - "../common/definitions.json" verbatim, for a schema without `$id`.
    The schema being validated needs no registration of its own: the
    validator anchors it as the resolver root, which covers its `$id` and
    local `#/$defs/...` refs.
    """
    global _registry
    if not HAS_JSONSCHEMA:
        return None

    if _registry is None:
        contracts_dir = _get_contracts_dir()
        resources = []
        for rel_dir in ("commands", "responses", "common"):
            for path in sorted((contracts_dir / rel_dir).glob("*.json")):
                resource = Resource.from_contents(
                    _load_schema(f"{rel_dir}/{path.name}"),
                    default_specification=DRAFT202012,
                )
                resources.append((path.name, resource))
                if rel_dir == "common":
                    resources.append((f"common/{path.name}", resource))
                    resources.append((f"../common/{path.name}", resource))
        _registry = Registry().with_resources(resources)
    return _registry


def validate_command(command_type: str, params: Dict[str, Any], raise_on_error: bool = True) -> bool:
    """
    Validate command parameters against the schema.

    Args:
        command_type: The command type (e.g., "create_object")
        params: The parameters to validate
        raise_on_error: If True, raises ValidationError on failure

    Returns:
        True if valid, False if invalid (when raise_on_error=False)

    Raises:
        jsonschema.ValidationError: If validation fails and raise_on_error=True
        FileNotFoundError: If schema file not found
    """
    if not HAS_JSONSCHEMA:
        logger.debug(f"Skipping validation for {command_type} (jsonschema not installed)")
        return True

    schema_path = f"commands/{command_type}.json"

    try:
        schema = _load_schema(schema_path)

        validator = Draft202012Validator(schema, registry=_get_registry())
        validator.validate(params)

        logger.debug(f"Validation passed for {command_type}")
        return True

    except jsonschema.ValidationError as e:
        logger.error(f"Validation failed for {command_type}: {e.message}")
        if raise_on_error:
            raise
        return False
    except FileNotFoundError:
        logger.warning(f"No schema found for {command_type}, skipping validation")
        return True


def validate_response(command_type: str, response: Dict[str, Any], raise_on_error: bool = True) -> bool:
    """
    Validate response data against the schema.

    Args:
        command_type: The command type that generated this response
        response: The response data to validate
        raise_on_error: If True, raises ValidationError on failure

    Returns:
        True if valid, False if invalid (when raise_on_error=False)
    """
    if not HAS_JSONSCHEMA:
        return True

    # Map command types to response schemas
    response_schema_map = {
        "create_object": "object_info.json",
        "modify_object": "object_info.json",
        "get_object_info": "object_info.json",
        "get_object_attributes": "object_attributes.json",
        "update_object_attributes": "object_attributes.json",
        "analyze_objects": "analyze_objects_result.json",
        "measure_objects": "measure_result.json",
        # get_selected_objects_info is deliberately unmapped: it returns
        # {"selected_objects": [...]}, which no current response schema
        # describes (object_info.json would reject it on every call).
        "get_document_summary": "document_summary.json",
        "get_objects": "get_objects_result.json",
        "delete_object": "delete_result.json",
        "select_objects": "select_result.json",
        "create_layer": "layer_info.json",
        "delete_layer": "delete_result.json",
        "get_or_set_current_layer": "layer_info.json",
        "execute_rhinoscript_python_code": "execute_script_result.json",
        "capture_viewport": "capture_viewport_result.json",
        "describe_capabilities": "capabilities.json",
    }

    schema_name = response_schema_map.get(command_type)
    if not schema_name:
        logger.debug(f"No response schema for {command_type}")
        return True

    schema_path = f"responses/{schema_name}"

    try:
        schema = _load_schema(schema_path)

        validator = Draft202012Validator(schema, registry=_get_registry())
        validator.validate(response)

        logger.debug(f"Response validation passed for {command_type}")
        return True

    except jsonschema.ValidationError as e:
        logger.error(f"Response validation failed for {command_type}: {e.message}")
        if raise_on_error:
            raise
        return False
    except FileNotFoundError:
        logger.warning(f"No response schema found for {command_type}")
        return True


def validate_protocol_command(data: Dict[str, Any], raise_on_error: bool = True) -> bool:
    """
    Validate a full protocol command (type + params envelope).

    Args:
        data: The full command with "type" and "params" keys
        raise_on_error: If True, raises on validation failure

    Returns:
        True if valid
    """
    if not HAS_JSONSCHEMA:
        return True

    # Validate envelope structure
    if "type" not in data:
        if raise_on_error:
            raise ValueError("Command missing 'type' field")
        return False

    if "params" not in data:
        if raise_on_error:
            raise ValueError("Command missing 'params' field")
        return False

    # Validate params against command schema
    return validate_command(data["type"], data["params"], raise_on_error)


def validate_protocol_response(data: Dict[str, Any], raise_on_error: bool = True) -> bool:
    """
    Validate a protocol response envelope.

    Args:
        data: The response with "status" and "result"/"message" keys
        raise_on_error: If True, raises on validation failure

    Returns:
        True if valid
    """
    if not HAS_JSONSCHEMA:
        return True

    if "status" not in data:
        if raise_on_error:
            raise ValueError("Response missing 'status' field")
        return False

    if data["status"] == "error":
        if "message" not in data:
            if raise_on_error:
                raise ValueError("Error response missing 'message' field")
            return False
        return True

    if data["status"] == "success":
        if "result" not in data:
            if raise_on_error:
                raise ValueError("Success response missing 'result' field")
            return False
        return True

    if raise_on_error:
        raise ValueError(f"Invalid status: {data['status']}")
    return False
