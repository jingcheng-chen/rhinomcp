#!/usr/bin/env python3
"""
Test script to validate JSON schemas and example payloads.

Run with: python3 contracts/test_schemas.py
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("Please install jsonschema: pip install jsonschema")
    sys.exit(1)

CONTRACTS_DIR = Path(__file__).parent


def load_schema_with_refs(schema_path: str) -> dict:
    """
    Load a JSON schema and inline all $ref references to common/definitions.json.
    This avoids complex ref resolution issues.
    """
    with open(CONTRACTS_DIR / schema_path) as f:
        schema = json.load(f)

    # Load common definitions
    with open(CONTRACTS_DIR / "common" / "definitions.json") as f:
        definitions = json.load(f)

    # Add definitions to schema
    if "$defs" not in schema:
        schema["$defs"] = {}

    # Merge common definitions
    for key, value in definitions.get("$defs", {}).items():
        schema["$defs"][f"common_{key}"] = value

    # Replace refs to common/definitions.json with local refs
    schema_str = json.dumps(schema)
    schema_str = schema_str.replace("../common/definitions.json#/$defs/", "#/$defs/common_")
    schema = json.loads(schema_str)

    return schema


def validate(schema_path: str, instance: dict) -> bool:
    """Validate an instance against a schema."""
    try:
        schema = load_schema_with_refs(schema_path)
        validator = Draft202012Validator(schema)

        errors = list(validator.iter_errors(instance))
        if errors:
            print(f"  FAIL: {schema_path}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"    - {error.message}")
            return False

        print(f"  PASS: {schema_path}")
        return True
    except Exception as e:
        print(f"  ERROR: {schema_path} - {e}")
        return False


def test_create_object_commands():
    """Test create_object command schemas."""
    print("\n=== Testing create_object commands ===")

    valid_examples = [
        # POINT
        {"type": "POINT", "params": {"x": 0, "y": 0, "z": 0}},
        # LINE
        {"type": "LINE", "params": {"start": [0, 0, 0], "end": [1, 1, 1]}},
        # BOX
        {"type": "BOX", "params": {"width": 1.0, "length": 2.0, "height": 3.0}},
        # BOX with optional fields
        {
            "type": "BOX",
            "name": "MyBox",
            "color": [255, 0, 0],
            "params": {"width": 1.0, "length": 2.0, "height": 3.0},
            "translation": [10, 0, 0]
        },
        # SPHERE
        {"type": "SPHERE", "params": {"radius": 5.0}},
        # CIRCLE
        {"type": "CIRCLE", "params": {"center": [0, 0, 0], "radius": 2.5}},
        # CURVE
        {"type": "CURVE", "params": {"points": [[0, 0, 0], [1, 1, 0], [2, 0, 0]], "degree": 2}},
        # CYLINDER
        {"type": "CYLINDER", "params": {"radius": 1.0, "height": 5.0, "cap": True}},
        # CONE
        {"type": "CONE", "params": {"radius": 2.0, "height": 4.0}},
    ]

    all_passed = True
    for i, example in enumerate(valid_examples):
        obj_type = example.get("type", "?")
        print(f"  Testing {obj_type}...", end=" ")
        if not validate("commands/create_object.json", example):
            all_passed = False

    return all_passed


def test_modify_object_commands():
    """Test modify_object command schemas."""
    print("\n=== Testing modify_object commands ===")

    valid_examples = [
        {"id": "12345678-1234-1234-1234-123456789012"},
        {"name": "MyObject"},
        {"id": "12345678-1234-1234-1234-123456789012", "new_name": "RenamedObject"},
        {"name": "MyObject", "new_color": [0, 255, 0]},
        {"id": "12345678-1234-1234-1234-123456789012", "translation": [1, 2, 3]},
        {"name": "Box1", "rotation": [0, 0, 1.57], "scale": [2, 2, 2]},
    ]

    all_passed = True
    for example in valid_examples:
        if not validate("commands/modify_object.json", example):
            all_passed = False

    return all_passed


def test_delete_object_commands():
    """Test delete_object command schemas."""
    print("\n=== Testing delete_object commands ===")

    valid_examples = [
        {"id": "12345678-1234-1234-1234-123456789012"},
        {"name": "MyObject"},
        {"all": True},
    ]

    all_passed = True
    for example in valid_examples:
        if not validate("commands/delete_object.json", example):
            all_passed = False

    return all_passed


def test_select_objects_commands():
    """Test select_objects command schemas."""
    print("\n=== Testing select_objects commands ===")

    valid_examples = [
        {"filters": {}},
        {"filters": {"name": ["Object1", "Object2"]}},
        {"filters": {"color": [255, 0, 0]}},
        {"filters": {"name": ["Box"], "category": ["furniture"]}, "filters_type": "and"},
        {"filters": {"category": ["walls", "floors"]}, "filters_type": "or"},
    ]

    all_passed = True
    for example in valid_examples:
        if not validate("commands/select_objects.json", example):
            all_passed = False

    return all_passed


def test_layer_commands():
    """Test layer command schemas."""
    print("\n=== Testing layer commands ===")

    all_passed = True

    # create_layer
    print("  create_layer:")
    create_examples = [
        {},
        {"name": "Layer 1"},
        {"name": "Layer 2", "color": [100, 150, 200]},
        {"name": "Sublayer", "parent": "Parent Layer"},
    ]
    for example in create_examples:
        if not validate("commands/create_layer.json", example):
            all_passed = False

    # delete_layer
    print("  delete_layer:")
    delete_examples = [
        {"name": "Layer 1"},
        {"guid": "12345678-1234-1234-1234-123456789012"},
    ]
    for example in delete_examples:
        if not validate("commands/delete_layer.json", example):
            all_passed = False

    # get_or_set_current_layer
    print("  get_or_set_current_layer:")
    layer_examples = [
        {},
        {"name": "Default"},
        {"guid": "12345678-1234-1234-1234-123456789012"},
    ]
    for example in layer_examples:
        if not validate("commands/get_or_set_current_layer.json", example):
            all_passed = False

    return all_passed


def test_other_commands():
    """Test other command schemas."""
    print("\n=== Testing other commands ===")

    all_passed = True

    # execute_rhinoscript_python_code
    print("  execute_rhinoscript_python_code:")
    if not validate("commands/execute_rhinoscript_python_code.json", {"code": "print('hello')"}):
        all_passed = False

    # get_document_info
    print("  get_document_info:")
    if not validate("commands/get_document_info.json", {}):
        all_passed = False

    # get_selected_objects_info
    print("  get_selected_objects_info:")
    if not validate("commands/get_selected_objects_info.json", {}):
        all_passed = False

    # get_object_info
    print("  get_object_info:")
    if not validate("commands/get_object_info.json", {"id": "12345678-1234-1234-1234-123456789012"}):
        all_passed = False
    if not validate("commands/get_object_info.json", {"name": "MyObject"}):
        all_passed = False

    return all_passed


def test_responses():
    """Test response schemas."""
    print("\n=== Testing response schemas ===")

    all_passed = True

    # Object info
    print("  object_info:")
    object_info = {
        "id": "12345678-1234-1234-1234-123456789012",
        "name": "MyBox",
        "type": "BOX",
        "layer": "Default",
        "material": "-1",
        "color": {"r": 255, "g": 0, "b": 0},
        "bounding_box": [[-1, -1, -1], [1, 1, 1]],
        "geometry": {}
    }
    if not validate("responses/object_info.json", object_info):
        all_passed = False

    # Select result
    print("  select_result:")
    select_result = {"count": 5}
    if not validate("responses/select_result.json", select_result):
        all_passed = False

    # Delete result
    print("  delete_result:")
    delete_result = {"id": "12345678-1234-1234-1234-123456789012", "name": "Deleted", "deleted": True}
    if not validate("responses/delete_result.json", delete_result):
        all_passed = False

    # Execute script result
    print("  execute_script_result:")
    script_result = {"success": True, "output": "Hello from Rhino"}
    if not validate("responses/execute_script_result.json", script_result):
        all_passed = False

    # Layer info
    print("  layer_info:")
    layer_info = {
        "id": "12345678-1234-1234-1234-123456789012",
        "name": "Default",
        "color": {"r": 0, "g": 0, "b": 0},
        "parent": "00000000-0000-0000-0000-000000000000"
    }
    if not validate("responses/layer_info.json", layer_info):
        all_passed = False

    return all_passed


def test_invalid_examples():
    """Test that invalid examples are rejected."""
    print("\n=== Testing invalid examples (should fail) ===")

    invalid_examples = [
        # Missing required field
        ("commands/create_object.json", {"type": "BOX"}, "Missing params"),
        ("commands/create_object.json", {"params": {"width": 1}}, "Missing type"),
        # Invalid type enum
        ("commands/create_object.json", {"type": "INVALID", "params": {}}, "Invalid type"),
        # Missing code
        ("commands/execute_rhinoscript_python_code.json", {}, "Missing code"),
    ]

    all_rejected = True
    for schema_path, example, description in invalid_examples:
        try:
            schema = load_schema_with_refs(schema_path)
            validator = Draft202012Validator(schema)
            errors = list(validator.iter_errors(example))

            if errors:
                print(f"  CORRECTLY REJECTED: {description}")
            else:
                print(f"  INCORRECTLY ACCEPTED: {description}")
                all_rejected = False
        except Exception as e:
            print(f"  ERROR checking {description}: {e}")
            all_rejected = False

    return all_rejected


def main():
    """Run all tests."""
    print("RhinoMCP Schema Validation Tests")
    print("=" * 40)

    results = []
    results.append(("create_object", test_create_object_commands()))
    results.append(("modify_object", test_modify_object_commands()))
    results.append(("delete_object", test_delete_object_commands()))
    results.append(("select_objects", test_select_objects_commands()))
    results.append(("layer commands", test_layer_commands()))
    results.append(("other commands", test_other_commands()))
    results.append(("responses", test_responses()))
    results.append(("invalid rejection", test_invalid_examples()))

    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
