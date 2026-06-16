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
        # CURVE with explicit degree
        {"type": "CURVE", "params": {"points": [[0, 0, 0], [1, 1, 0], [2, 0, 0]], "degree": 2}},
        # CURVE relying on default degree (3 points -> handler clamps to degree 2)
        {"type": "CURVE", "params": {"points": [[0, 0, 0], [1, 1, 0], [2, 0, 0]]}},
        # CURVE with 4 points and default degree (-> 3)
        {"type": "CURVE", "params": {"points": [[0, 0, 0], [1, 1, 0], [2, 0, 0], [3, 0, 0]]}},
        # CYLINDER
        {"type": "CYLINDER", "params": {"radius": 1.0, "height": 5.0, "cap": True}},
        # CYLINDER without cap (defaults to true)
        {"type": "CYLINDER", "params": {"radius": 1.0, "height": 5.0}},
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


def test_new_commands():
    """Positive cases for the commands added in the schema-coverage pass."""
    print("\n=== Testing newly added command schemas ===")

    GUID = "12345678-1234-1234-1234-123456789012"
    cases = [
        ("commands/boolean_union.json", {"object_ids": [GUID, GUID]}),
        ("commands/boolean_difference.json", {"base_id": GUID, "subtract_ids": [GUID]}),
        ("commands/boolean_intersection.json", {"object_ids": [GUID, GUID]}),
        ("commands/create_objects.json", {"Box1": {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}}}),
        ("commands/execute_rhinocommon_csharp_code.json", {"code": "doc.Objects.AddPoint(0,0,0);"}),
        ("commands/extrude_curve.json", {"curve_id": GUID, "direction": [0, 0, 10]}),
        ("commands/loft.json", {"curve_ids": [GUID, GUID]}),
        ("commands/modify_objects.json", {"objects": [{"id": GUID, "new_name": "X"}]}),
        ("commands/offset_curve.json", {"curve_id": GUID, "distance": 1.5}),
        ("commands/pipe.json", {"curve_id": GUID, "radius": 0.5}),
        ("commands/sweep1.json", {"rail_id": GUID, "profile_ids": [GUID]}),
        ("commands/get_object_attributes.json", {"id": GUID}),
        ("commands/update_object_attributes.json", {"id": GUID, "user_strings": {"PartNo": "A-100", "Count": 3}}),
        ("commands/update_object_attributes.json", {"name": "Box1", "layer": "Default", "visible": True}),
        ("commands/update_object_attributes.json", {"id": GUID, "delete_user_strings": ["PartNo"]}),
        ("commands/update_object_attributes.json", {"id": GUID, "material_index": -1}),
        ("commands/analyze_objects.json", {"id": GUID}),
        ("commands/analyze_objects.json", {"object_ids": [GUID]}),
        ("commands/analyze_objects.json", {"selected": True}),
        ("commands/measure_objects.json", {"object_ids": [GUID, GUID]}),
        ("commands/gh_create_document.json", {"new_if_missing": True, "make_active": True, "open_canvas": True}),
        ("commands/gh_get_document_info.json", {}),
        ("commands/gh_search_components.json", {"query": "addition", "limit": 10}),
        ("commands/gh_batch_search_components.json", {"queries": ["Circle", "Number Slider"], "max_matches": 5}),
        ("commands/gh_list_component_categories.json", {}),
        ("commands/gh_get_available_components.json", {"category": "Curve", "include_description": True, "limit": 25}),
        ("commands/gh_get_component_type_info.json", {"name": "Circle"}),
        ("commands/gh_batch_get_component_type_info.json", {"components": [{"name": "Circle"}, {"guid": GUID}]}),
        ("commands/gh_get_graph.json", {"graph_id": "TestGraph", "include_values": True, "max_items": 5}),
        ("commands/gh_clear_graph.json", {"graph_id": "TestGraph", "include_groups": True, "recompute": False}),
        ("commands/gh_list_components.json", {"category": "Curve", "limit": 20}),
        ("commands/gh_get_component_info.json", {"instance_id": GUID}),
        ("commands/gh_get_canvas_state.json", {"include_connections": True, "include_values": False, "max_items": 5}),
        ("commands/gh_capture_preview.json", {"viewport": "perspective", "width": 800, "height": 600, "graph_id": "TestGraph", "padding_factor": 1.2}),
        ("commands/gh_run_solution.json", {"expire_all": True}),
        ("commands/gh_expire_solution.json", {"component_ids": [GUID], "recompute": True}),
        ("commands/gh_build_graph.json", {
            "components": [
                {"alias": "slider_a", "component_name": "Number Slider", "nickname": "A", "value": 3.5, "min": 0, "max": 10},
                {"alias": "add", "component_name": "Addition", "nickname": "Add"},
                {"alias": "by_guid", "component_guid": GUID, "nickname": "ByGuid"}
            ],
            "connections": [{"source": "slider_a", "target": "add", "target_input_index": 0}],
            "values": [{"target": "slider_a", "value": 4.0, "decimals": 1}],
            "preview_updates": {"enabled": False},
            "preview_policy": {"mode": "only", "targets": ["add"], "scope": ["slider_a", "add"]},
            "groups": [{"name": "Controls", "targets": ["slider_a"], "color": [180, 220, 255]}],
            "layout": {"enabled": True, "start_position": [40, 40], "x_spacing": 220, "max_columns": 6},
            "graph_id": "TestGraph",
            "recompute": True,
            "rollback_on_error": True,
            "open_canvas": True
        }),
        ("commands/gh_add_component.json", {"component_guid": GUID, "nickname": "ByGuid"}),
        ("commands/gh_mutate_graph.json", {
            "graph_id": "TestGraph",
            "operations": [
                {"op": "create", "alias": "height", "component_name": "Number Slider", "value": 8, "min": 0, "max": 20, "role": "control"},
                {"op": "create", "alias": "by_guid", "guid": GUID},
                {"op": "update", "target": "cylinder", "preview": False},
                {"op": "connect", "source": "height", "target": "cap", "target_input_index": 0},
                {"op": "recompute"}
            ],
            "preview_policy": {"mode": "only", "targets": ["cap"]},
            "groups": [{"name": "Output", "targets": ["cap"], "color": [180, 220, 255]}],
            "layout": {"enabled": True, "targets": ["height", "cap"], "max_columns": 6},
            "verify": {
                "run_solution": True,
                "expect_no_runtime_warnings": True,
                "outputs": [{
                    "target": "cap",
                    "output_index": 0,
                    "expect_count_min": 1,
                    "expect_count_exact": 1,
                    "expect_type": "Brep",
                    "expect_all_type": "Brep",
                    "expect_all_solid": True
                }]
            },
            "fail_on_verification_error": True,
            "recompute": True,
            "rollback_on_error": True,
            "open_canvas": True
        }),
        ("commands/gh_mutate_graph.json", {
            "graph_id": "ExistingGraph",
            "operations": [
                {"op": "disconnect", "source": GUID, "source_output_name": "G", "target": GUID, "target_input_name": "L"},
                {"op": "create", "alias": "flatten_inserted", "component_name": "Flatten Tree", "nickname": "Flatten"},
                {"op": "connect", "source": GUID, "source_output_name": "G", "target": "flatten_inserted"},
                {"op": "connect", "source": "flatten_inserted", "target": GUID, "target_input_name": "L"},
                {"op": "recompute"}
            ],
            "layout": {"enabled": True, "targets": [GUID, "flatten_inserted"], "max_columns": 4},
            "recompute": True,
            "rollback_on_error": True
        }),
        ("commands/gh_add_component.json", {"component_name": "Number Slider", "position": [20, 40], "nickname": "Radius", "value": 5, "min": 0, "max": 10}),
        ("commands/gh_delete_component.json", {"nickname": "Radius"}),
        ("commands/gh_layout_components.json", {"component_ids": [GUID], "start_position": [40, 40], "x_spacing": 220, "y_spacing": 90, "recompute": True}),
        ("commands/gh_connect_components.json", {"source_instance_id": GUID, "source_output_index": 0, "target_instance_id": GUID, "target_input_name": "Radius"}),
        ("commands/gh_disconnect_components.json", {"target_instance_id": GUID, "target_input_index": 0, "disconnect_all": True}),
        ("commands/gh_set_parameter_value.json", {"nickname": "Radius", "value": 7.5, "input_index": 0}),
        ("commands/gh_get_parameter_value.json", {"instance_id": GUID, "output_index": 0, "max_items": 10}),
        ("commands/gh_update_component.json", {"instance_id": GUID, "new_nickname": "Radius2", "position": [100, 200], "preview": False}),
        ("commands/gh_clear_canvas.json", {"include_groups": True, "recompute": False}),
        ("commands/undo.json", {}),
        ("commands/undo.json", {"steps": 3}),
        ("commands/redo.json", {}),
    ]

    all_passed = True
    for path, example in cases:
        if not validate(path, example):
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

    # get_document_summary
    print("  get_document_summary:")
    if not validate("commands/get_document_summary.json", {}):
        all_passed = False

    # get_objects
    print("  get_objects:")
    if not validate("commands/get_objects.json", {}):
        all_passed = False
    if not validate("commands/get_objects.json", {"limit": 100, "offset": 0}):
        all_passed = False
    if not validate("commands/get_objects.json", {"layer_filter": "Default", "type_filter": "CURVE"}):
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

    # run_command
    print("  run_command:")
    if not validate("commands/run_command.json", {"command": "_Box 0,0,0 10,10,10"}):
        all_passed = False
    if not validate("commands/run_command.json", {"command": "_SelAll", "echo": True}):
        all_passed = False

    # get_commands
    print("  get_commands:")
    if not validate("commands/get_commands.json", {}):
        all_passed = False
    if not validate("commands/get_commands.json", {"filter": "boolean", "loaded_only": False}):
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
    # Deleting an unnamed object reports the "(unnamed)" fallback, never null.
    # name is typed as a string, so a null is a regression: it made deleting a
    # nameless object fail response validation under strict mode.
    unnamed_delete = {"id": "12345678-1234-1234-1234-123456789012", "name": "(unnamed)", "deleted": True}
    if not validate("responses/delete_result.json", unnamed_delete):
        all_passed = False
    delete_validator = Draft202012Validator(load_schema_with_refs("responses/delete_result.json"))
    null_name = {"id": "12345678-1234-1234-1234-123456789012", "name": None, "deleted": True}
    if not list(delete_validator.iter_errors(null_name)):
        print("  FAIL: delete_result accepted a null name")
        all_passed = False
    else:
        print("  delete_result rejects a null name")

    # Execute script result
    print("  execute_script_result:")
    script_result = {"success": True, "output": "Hello from Rhino"}
    if not validate("responses/execute_script_result.json", script_result):
        all_passed = False

    # Capabilities (describe_capabilities). The command list and perception flags
    # may be empty; the shape must still hold.
    print("  capabilities:")
    capabilities = {
        "version": "0.3.1",
        "command_count": 2,
        "commands": [
            {"name": "create_object", "read_only": False},
            {"name": "get_objects", "read_only": True},
        ],
        "perception": {
            "description": "Mutating commands accept opt-in envelope flags.",
            "envelope_flags": [
                {"flag": "include_delta", "attaches": "_delta",
                 "description": "Attaches a change-delta."},
                {"flag": "include_health", "attaches": "_health",
                 "description": "Attaches a geometry-health report."},
            ],
        },
    }
    if not validate("responses/capabilities.json", capabilities):
        all_passed = False
    minimal_caps = {"version": "0", "command_count": 0, "commands": [],
                    "perception": {"description": "none", "envelope_flags": []}}
    if not validate("responses/capabilities.json", minimal_caps):
        all_passed = False
    caps_validator = Draft202012Validator(load_schema_with_refs("responses/capabilities.json"))
    bad_caps = [
        # a command missing read_only
        {"version": "0.3.1", "command_count": 1, "commands": [{"name": "x"}],
         "perception": {"description": "d", "envelope_flags": []}},
        # read_only not a boolean
        {"version": "0.3.1", "command_count": 1, "commands": [{"name": "x", "read_only": "yes"}],
         "perception": {"description": "d", "envelope_flags": []}},
        # unknown top-level field
        {"version": "0.3.1", "command_count": 0, "commands": [],
         "perception": {"description": "d", "envelope_flags": []}, "extra": 1},
        # missing perception
        {"version": "0.3.1", "command_count": 0, "commands": []},
        # envelope flag missing attaches
        {"version": "0.3.1", "command_count": 0, "commands": [],
         "perception": {"description": "d", "envelope_flags": [{"flag": "include_delta", "description": "d"}]}},
    ]
    for bad in bad_caps:
        if not list(caps_validator.iter_errors(bad)):
            print(f"  FAIL: capabilities accepted invalid payload {bad}")
            all_passed = False
    print("  capabilities negatives correctly rejected")

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

    # Object attributes
    print("  object_attributes:")
    object_attributes = {
        "id": "12345678-1234-1234-1234-123456789012",
        "name": "MyBox",
        "type": "BOX",
        "layer": {
            "index": 0,
            "id": "12345678-1234-1234-1234-123456789012",
            "name": "Default",
            "full_path": "Default",
        },
        "color": {"r": 255, "g": 0, "b": 0},
        "color_source": "ColorFromObject",
        "material_index": -1,
        "material_source": "MaterialFromLayer",
        "visible": True,
        "locked": False,
        "hidden": False,
        "normal": True,
        "user_strings": {"PartNo": "A-100"},
    }
    if not validate("responses/object_attributes.json", object_attributes):
        all_passed = False

    # Analyze objects
    print("  analyze_objects_result:")
    analyze_result = {
        "object_count": 1,
        "analyses": [
            {
                "id": "12345678-1234-1234-1234-123456789012",
                "name": "Line1",
                "type": "LINE",
                "layer": "Default",
                "valid": True,
                "validity_log": None,
                "bounding_box": [[0, 0, 0], [10, 0, 0]],
                "bbox_dimensions": [10, 0, 0],
                "metrics": {
                    "length": 10,
                    "is_closed": False,
                    "start_point": [0, 0, 0],
                    "end_point": [10, 0, 0],
                },
            }
        ],
    }
    if not validate("responses/analyze_objects_result.json", analyze_result):
        all_passed = False

    # Change delta (perception). created/deleted may be empty (a delete creates
    # nothing), so the schema must accept empty arrays.
    print("  change_delta:")
    GUID = "12345678-1234-1234-1234-123456789012"
    delta_created = {
        "created_count": 1,
        "deleted_count": 0,
        "count_before": 0,
        "count_after": 1,
        "created_ids": [GUID],
        "deleted_ids": [],
        "truncated": False,
    }
    if not validate("responses/change_delta.json", delta_created):
        all_passed = False
    # Truncated shape: counts present, id arrays omitted, truncated true.
    delta_truncated = {
        "created_count": 5000,
        "deleted_count": 0,
        "count_before": 0,
        "count_after": 5000,
        "truncated": True,
    }
    if not validate("responses/change_delta.json", delta_truncated):
        all_passed = False

    # Negative: the schema must actually constrain (not be vacuously permissive).
    delta_schema = load_schema_with_refs("responses/change_delta.json")
    delta_validator = Draft202012Validator(delta_schema)
    bad_deltas = [
        # bad guid in an id list
        {"created_count": 1, "deleted_count": 0, "count_before": 0, "count_after": 1,
         "created_ids": ["not-a-guid"], "deleted_ids": [], "truncated": False},
        # unknown field
        {"created_count": 0, "deleted_count": 0, "count_before": 0, "count_after": 0,
         "truncated": False, "modified_count": 3},
        # missing required truncated
        {"created_count": 0, "deleted_count": 0, "count_before": 0, "count_after": 0},
        # missing required count
        {"created_count": 0, "deleted_count": 0, "count_after": 0, "truncated": False},
    ]
    for bad in bad_deltas:
        if not list(delta_validator.iter_errors(bad)):
            print(f"  FAIL: change_delta accepted invalid payload {bad}")
            all_passed = False
    print("  change_delta negatives correctly rejected")

    # Change health (perception). A clean write has an empty issues array; an
    # invalid write lists each bad object with its validity reason.
    print("  change_health:")
    health_clean = {
        "checked_count": 3,
        "invalid_count": 0,
        "issues": [],
        "truncated": False,
    }
    if not validate("responses/change_health.json", health_clean):
        all_passed = False
    health_issue = {
        "checked_count": 2,
        "invalid_count": 1,
        "issues": [{"id": GUID, "reason": "Line points are coincident."}],
        "truncated": False,
    }
    if not validate("responses/change_health.json", health_issue):
        all_passed = False

    # Negative: the schema must actually constrain.
    health_schema = load_schema_with_refs("responses/change_health.json")
    health_validator = Draft202012Validator(health_schema)
    bad_healths = [
        # bad guid in an issue
        {"checked_count": 1, "invalid_count": 1,
         "issues": [{"id": "not-a-guid", "reason": "x"}], "truncated": False},
        # issue missing its reason
        {"checked_count": 1, "invalid_count": 1,
         "issues": [{"id": GUID}], "truncated": False},
        # issue carrying an unknown field
        {"checked_count": 1, "invalid_count": 1,
         "issues": [{"id": GUID, "reason": "x", "severity": "high"}], "truncated": False},
        # unknown top-level field
        {"checked_count": 0, "invalid_count": 0, "issues": [], "truncated": False,
         "warnings": 2},
        # missing required issues array
        {"checked_count": 0, "invalid_count": 0, "truncated": False},
    ]
    for bad in bad_healths:
        if not list(health_validator.iter_errors(bad)):
            print(f"  FAIL: change_health accepted invalid payload {bad}")
            all_passed = False
    print("  change_health negatives correctly rejected")
    # Measure result
    print("  measure_result:")
    measure_result = {
        "object_a": GUID,
        "object_b": GUID,
        "clash": False,
        "intersection_count": 0,
        "bbox_gap": 3.5,
        "method": "brep",
    }
    if not validate("responses/measure_result.json", measure_result):
        all_passed = False
    # Negative: an unknown method and a missing field must be rejected.
    measure_schema = load_schema_with_refs("responses/measure_result.json")
    measure_validator = Draft202012Validator(measure_schema)
    bad_measures = [
        {"object_a": GUID, "object_b": GUID, "clash": False,
         "intersection_count": 0, "bbox_gap": 1.0, "method": "voxel"},
        {"object_a": GUID, "object_b": GUID, "clash": False,
         "intersection_count": 0, "method": "brep"},
    ]
    for bad in bad_measures:
        if not list(measure_validator.iter_errors(bad)):
            print(f"  FAIL: measure_result accepted invalid payload {bad}")
            all_passed = False
    print("  measure_result negatives correctly rejected")

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
        # Missing run_command.command
        ("commands/run_command.json", {}, "run_command missing command"),
        ("commands/run_command.json", {"command": ""}, "run_command empty command"),
        # Unknown property on get_commands
        ("commands/get_commands.json", {"bogus": 1}, "get_commands unknown field"),
        # delete_object: all=false is meaningless and must be rejected
        ("commands/delete_object.json", {"all": False}, "delete_object all=false"),
        # delete_object: unknown properties rejected
        ("commands/delete_object.json", {"id": "12345678-1234-1234-1234-123456789012", "bogus": 1}, "delete_object unknown field"),
        # delete_object: mixed selectors (id + all) — ambiguous, would silently delete-all
        ("commands/delete_object.json", {"id": "12345678-1234-1234-1234-123456789012", "all": True}, "delete_object mixed id+all"),
        ("commands/delete_object.json", {"name": "Box1", "all": True}, "delete_object mixed name+all"),
        # create_object: params discriminated by type — sphere params on a BOX must fail
        ("commands/create_object.json", {"type": "BOX", "params": {"radius": 1}}, "create_object BOX with sphere params"),
        # create_object: PIPE removed from enum (use the dedicated `pipe` tool instead)
        ("commands/create_object.json", {"type": "PIPE", "params": {"curve_id": "x", "radius": 1}}, "create_object PIPE removed"),
        # create_object: top-level additionalProperties: false
        ("commands/create_object.json", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}, "bogus": 1}, "create_object unknown top-level field"),
        # New schemas reject obvious mistakes
        ("commands/boolean_union.json", {"object_ids": ["only-one"]}, "boolean_union not enough ids (and bad GUID)"),
        ("commands/extrude_curve.json", {"curve_id": "12345678-1234-1234-1234-123456789012", "direction": [0, 0, 0]}, "extrude_curve zero direction"),
        ("commands/pipe.json", {"curve_id": "12345678-1234-1234-1234-123456789012", "radius": 0}, "pipe non-positive radius"),
        ("commands/undo.json", {"steps": 0}, "undo zero steps"),
        ("commands/loft.json", {"curve_ids": ["12345678-1234-1234-1234-123456789012"]}, "loft single curve"),
        ("commands/modify_objects.json", {"objects": [{"new_name": "X"}]}, "modify_objects no selector"),
        ("commands/modify_objects.json", {"objects": [{"id": "12345678-1234-1234-1234-123456789012"}], "all": False}, "modify_objects all=false"),
        ("commands/offset_curve.json", {"curve_id": "12345678-1234-1234-1234-123456789012", "distance": 0}, "offset_curve zero distance"),
        ("commands/get_object_attributes.json", {"id": "12345678-1234-1234-1234-123456789012", "bogus": 1}, "get_object_attributes unknown field"),
        ("commands/update_object_attributes.json", {"id": "12345678-1234-1234-1234-123456789012"}, "update_object_attributes no update fields"),
        ("commands/update_object_attributes.json", {"id": "12345678-1234-1234-1234-123456789012", "visible": False, "locked": True}, "update_object_attributes hidden and locked"),
        ("commands/update_object_attributes.json", {"id": "12345678-1234-1234-1234-123456789012", "user_strings": {"": "bad"}}, "update_object_attributes empty user string key"),
        ("commands/update_object_attributes.json", {"id": "12345678-1234-1234-1234-123456789012", "user_strings": {"nested": {"bad": True}}}, "update_object_attributes nested user string value"),
        ("commands/analyze_objects.json", {}, "analyze_objects no selector"),
        ("commands/analyze_objects.json", {"object_ids": []}, "analyze_objects empty object_ids"),
        ("commands/analyze_objects.json", {"id": "12345678-1234-1234-1234-123456789012", "selected": True}, "analyze_objects mixed selectors"),
        ("commands/analyze_objects.json", {"selected": False}, "analyze_objects selected=false"),
        ("commands/measure_objects.json", {"object_ids": ["12345678-1234-1234-1234-123456789012"]}, "measure_objects needs two ids"),
        ("commands/measure_objects.json", {"object_ids": ["12345678-1234-1234-1234-123456789012", "12345678-1234-1234-1234-123456789012", "12345678-1234-1234-1234-123456789012"]}, "measure_objects too many ids"),
        ("commands/measure_objects.json", {"object_ids": ["not-a-guid", "12345678-1234-1234-1234-123456789012"]}, "measure_objects bad guid"),
        ("commands/measure_objects.json", {"object_ids": ["12345678-1234-1234-1234-123456789012", "12345678-1234-1234-1234-123456789012"], "bogus": 1}, "measure_objects unknown field"),
        ("commands/gh_create_document.json", {"template_path": "example.gh"}, "gh_create_document unknown field"),
        ("commands/gh_batch_search_components.json", {"queries": []}, "gh_batch_search_components empty queries"),
        ("commands/gh_get_component_type_info.json", {}, "gh_get_component_type_info missing selector"),
        ("commands/gh_batch_get_component_type_info.json", {"components": []}, "gh_batch_get_component_type_info empty components"),
        ("commands/gh_batch_get_component_type_info.json", {"components": [{"name": ""}]}, "gh_batch_get_component_type_info empty name"),
        ("commands/gh_get_graph.json", {}, "gh_get_graph missing graph_id"),
        ("commands/gh_get_graph.json", {"graph_id": ""}, "gh_get_graph empty graph_id"),
        ("commands/gh_clear_graph.json", {}, "gh_clear_graph missing graph_id"),
        ("commands/gh_clear_graph.json", {"graph_id": "", "recompute": True}, "gh_clear_graph empty graph_id"),
        ("commands/gh_get_component_info.json", {}, "gh_get_component_info missing selector"),
        ("commands/gh_get_canvas_state.json", {"max_items": -1}, "gh_get_canvas_state negative max_items"),
        ("commands/gh_capture_preview.json", {"targets": []}, "gh_capture_preview empty targets"),
        ("commands/gh_capture_preview.json", {"width": 50}, "gh_capture_preview too narrow"),
        ("commands/gh_capture_preview.json", {"padding_factor": 0.5}, "gh_capture_preview bad padding"),
        ("commands/gh_run_solution.json", {"timeout_ms": 1000}, "gh_run_solution unknown timeout field"),
        ("commands/gh_build_graph.json", {"components": []}, "gh_build_graph empty components"),
        ("commands/gh_build_graph.json", {"components": [{"component_name": "Addition"}]}, "gh_build_graph component missing alias"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add"}]}, "gh_build_graph component missing selector"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "1bad", "component_name": "Addition"}]}, "gh_build_graph bad alias"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add", "component_name": "Addition"}], "connections": [{"source": "add"}]}, "gh_build_graph connection missing target"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add", "component_name": "Addition"}], "layout": {"x_spacing": 0}}, "gh_build_graph bad layout spacing"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add", "component_name": "Addition"}], "layout": {"max_columns": 0}}, "gh_build_graph bad layout max_columns"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add", "component_name": "Addition"}], "open_canvas": "yes"}, "gh_build_graph open_canvas not boolean"),
        ("commands/gh_build_graph.json", {"components": [{"alias": "add", "component_name": "Addition"}], "preview_policy": {"mode": "only"}}, "gh_build_graph preview policy missing targets"),
        ("commands/gh_mutate_graph.json", {"operations": []}, "gh_mutate_graph empty operations"),
        ("commands/gh_mutate_graph.json", {"operations": [{"target": "x"}]}, "gh_mutate_graph op missing op"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "rename", "target": "x"}]}, "gh_mutate_graph bad op"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "create", "alias": "bad alias", "component_name": "Panel"}]}, "gh_mutate_graph bad alias"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "update", "target": "x"}], "preview_policy": {"mode": "show"}}, "gh_mutate_graph preview policy missing targets"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "update", "target": "x"}], "layout": {"max_columns": 0}}, "gh_mutate_graph bad layout max_columns"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "update", "target": "x"}], "open_canvas": "yes"}, "gh_mutate_graph open_canvas not boolean"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "update", "target": "x"}], "verify": {"outputs": []}}, "gh_mutate_graph empty verify outputs"),
        ("commands/gh_mutate_graph.json", {"operations": [{"op": "recompute"}], "fail_on_verification_error": "yes"}, "gh_mutate_graph fail_on_verification_error not boolean"),
        ("commands/gh_add_component.json", {"position": [10, 20]}, "gh_add_component missing component selector"),
        ("commands/gh_add_component.json", {"component_name": "Circle", "position": [1, 2, 3]}, "gh_add_component bad position"),
        ("commands/gh_delete_component.json", {}, "gh_delete_component missing selector"),
        ("commands/gh_layout_components.json", {"component_ids": []}, "gh_layout_components empty component_ids"),
        ("commands/gh_layout_components.json", {"x_spacing": 0}, "gh_layout_components zero x spacing"),
        ("commands/gh_layout_components.json", {"start_position": [1, 2, 3]}, "gh_layout_components bad start position"),
        ("commands/gh_connect_components.json", {"source_instance_id": "bad", "target_instance_id": "12345678-1234-1234-1234-123456789012"}, "gh_connect_components bad source guid"),
        ("commands/gh_disconnect_components.json", {"disconnect_all": True}, "gh_disconnect_components missing target"),
        ("commands/gh_disconnect_components.json", {"target_instance_id": "12345678-1234-1234-1234-123456789012"}, "gh_disconnect_components missing source when not disconnect_all"),
        ("commands/gh_set_parameter_value.json", {"nickname": "Radius"}, "gh_set_parameter_value missing value"),
        ("commands/gh_get_parameter_value.json", {"nickname": "Radius", "output_index": -1}, "gh_get_parameter_value negative output"),
        ("commands/gh_update_component.json", {"instance_id": "12345678-1234-1234-1234-123456789012"}, "gh_update_component no updates"),
        ("commands/gh_clear_canvas.json", {"confirm": True}, "gh_clear_canvas unknown field"),
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


def test_contract_synchronization_across_tiers():
    """All three tiers must agree on the set of command names:

    - protocol.json command.type enum
    - Python: every send_command("<name>", ...) call in the tool wrappers
    - C#: every [McpCommand("<name>")] attribute in the plugin

    A mismatch means an LLM client can call a tool that the plugin doesn't
    understand, or a plugin handler that nothing routes to.
    """
    import re

    print("\n=== Testing contract sync across tiers ===")
    repo_root = CONTRACTS_DIR.parent

    with open(CONTRACTS_DIR / "protocol.json") as f:
        protocol = json.load(f)
    protocol_cmds = set(protocol["$defs"]["command"]["properties"]["type"]["enum"])

    # Python tools: scrape send_command("<name>") calls. We accept the
    # simple positional form because every wrapper uses it.
    py_pat = re.compile(
        r"""(?:send_command|_send|send_grasshopper_command)\(\s*["']([a-z_][a-z0-9_]*)["']"""
    )
    py_cmds: set[str] = set()
    tools_dir = repo_root / "server" / "src" / "rhinomcp" / "tools"
    for p in tools_dir.glob("*.py"):
        if p.name.startswith("_"):
            continue
        py_cmds.update(py_pat.findall(p.read_text()))

    # C# handlers: scrape [McpCommand("<name>")] attribute usages.
    cs_pat = re.compile(r'\[McpCommand\(\s*"([a-z_][a-z0-9_]*)"')
    cs_cmds: set[str] = set()
    funcs_dir = repo_root / "plugin" / "Functions"
    for p in funcs_dir.glob("*.cs"):
        cs_cmds.update(cs_pat.findall(p.read_text()))

    all_passed = True

    py_missing = sorted(py_cmds - protocol_cmds)
    if py_missing:
        print(f"  FAIL: Python wraps commands not in protocol enum: {py_missing}")
        all_passed = False

    cs_missing_in_protocol = sorted(cs_cmds - protocol_cmds)
    if cs_missing_in_protocol:
        print(f"  FAIL: C# handles commands not in protocol enum: {cs_missing_in_protocol}")
        all_passed = False

    protocol_missing_in_cs = sorted(protocol_cmds - cs_cmds)
    if protocol_missing_in_cs:
        print(f"  FAIL: protocol commands without a C# [McpCommand] handler: {protocol_missing_in_cs}")
        all_passed = False

    # Python-vs-C# is implicit (each checked against protocol), but call it
    # out for the most useful failure message.
    py_unhandled = sorted(py_cmds - cs_cmds)
    if py_unhandled:
        print(f"  FAIL: Python wrappers without a C# handler: {py_unhandled}")
        all_passed = False

    # Protocol-vs-Python: a command added to protocol.json + C# but missing
    # a Python wrapper would silently be unreachable from MCP clients.
    protocol_missing_in_py = sorted(protocol_cmds - py_cmds)
    if protocol_missing_in_py:
        print(f"  FAIL: protocol commands without a Python wrapper: {protocol_missing_in_py}")
        all_passed = False

    if all_passed:
        print(f"  PASS: {len(protocol_cmds)} commands in sync across protocol, Python, C#")
    return all_passed


def test_schema_coverage_against_protocol():
    """Every command in the protocol envelope must have a schema file in commands/."""
    print("\n=== Testing schema coverage matches protocol enum ===")

    with open(CONTRACTS_DIR / "protocol.json") as f:
        protocol = json.load(f)
    commands_in_protocol = set(protocol["$defs"]["command"]["properties"]["type"]["enum"])

    commands_dir = CONTRACTS_DIR / "commands"
    schema_files = {p.stem for p in commands_dir.glob("*.json")}

    missing_schemas = sorted(commands_in_protocol - schema_files)
    orphan_schemas = sorted(schema_files - commands_in_protocol)
    # capture_viewport / get_or_set_current_layer-style fixtures are still valid orphans
    # only if they sit in the enum — anything left over is genuinely orphaned.

    if missing_schemas:
        print(f"  FAIL: commands without schemas: {missing_schemas}")
    if orphan_schemas:
        print(f"  WARN: schema files without a protocol enum entry: {orphan_schemas}")

    if not missing_schemas:
        print(f"  PASS: all {len(commands_in_protocol)} protocol commands have schemas")
    return not missing_schemas


def test_protocol_envelope():
    """Test the {type, params} envelope from protocol.json against the dispatch table."""
    print("\n=== Testing protocol envelope ===")

    with open(CONTRACTS_DIR / "protocol.json") as f:
        protocol = json.load(f)
    envelope = protocol["$defs"]["command"]
    validator = Draft202012Validator(envelope)

    # Mirrors the C# dispatch table in plugin/RhinoMCPServer.cs.
    # Update both sides together when adding a command.
    expected_commands = [
        "create_object", "create_objects", "modify_object", "modify_objects",
        "delete_object", "get_object_info", "get_selected_objects_info",
        "get_object_attributes", "update_object_attributes",
        "analyze_objects", "measure_objects",
        "get_document_summary", "get_objects", "select_objects",
        "create_layer", "delete_layer", "get_or_set_current_layer",
        "execute_rhinoscript_python_code", "execute_rhinocommon_csharp_code",
        "capture_viewport", "undo", "redo",
        "boolean_union", "boolean_difference", "boolean_intersection",
        "loft", "extrude_curve", "sweep1", "offset_curve", "pipe",
        "project_curve", "intersect_curves", "split_curve",
        "run_command", "get_commands",
        "gh_create_document",
        "gh_get_document_info", "gh_search_components",
        "gh_batch_search_components", "gh_list_component_categories",
        "gh_get_available_components", "gh_get_component_type_info",
        "gh_batch_get_component_type_info",
        "gh_get_graph", "gh_clear_graph",
        "gh_list_components", "gh_get_component_info",
        "gh_get_canvas_state", "gh_capture_preview", "gh_run_solution", "gh_expire_solution",
        "gh_build_graph", "gh_mutate_graph", "gh_add_component", "gh_delete_component", "gh_layout_components", "gh_connect_components",
        "gh_disconnect_components", "gh_set_parameter_value",
        "gh_get_parameter_value", "gh_update_component", "gh_clear_canvas",
    ]

    all_passed = True

    for cmd in expected_commands:
        envelope_msg = {"type": cmd, "params": {}}
        errors = list(validator.iter_errors(envelope_msg))
        if errors:
            print(f"  FAIL: '{cmd}' rejected by envelope ({errors[0].message})")
            all_passed = False
        else:
            print(f"  PASS: '{cmd}'")

    # Negative: unknown command type must be rejected
    unknown = {"type": "totally_made_up_command", "params": {}}
    errors = list(validator.iter_errors(unknown))
    if not errors:
        print("  FAIL: envelope accepted an unknown command type")
        all_passed = False
    else:
        print("  CORRECTLY REJECTED: unknown command type")

    return all_passed


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
    results.append(("new commands", test_new_commands()))
    results.append(("other commands", test_other_commands()))
    results.append(("responses", test_responses()))
    results.append(("invalid rejection", test_invalid_examples()))
    results.append(("schema coverage", test_schema_coverage_against_protocol()))
    results.append(("contract sync (3 tiers)", test_contract_synchronization_across_tiers()))
    results.append(("protocol envelope", test_protocol_envelope()))

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
