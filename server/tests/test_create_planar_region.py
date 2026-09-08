"""Transport and schema tests for create_planar_region."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jsonschema import Draft202012Validator, RefResolver

from rhinomcp.tools.create_planar_region import create_planar_region


OUTER = "00000000-0000-0000-0000-000000000001"
INNER_A = "00000000-0000-0000-0000-000000000002"
INNER_B = "00000000-0000-0000-0000-000000000003"


@patch("rhinomcp.tools.create_planar_region.get_rhino_connection")
def test_forwards_typed_command_and_returns_topology(mock_get_connection):
    connection = MagicMock()
    connection.send_command.return_value = {
        "id": "region-id",
        "face_count": 1,
        "loop_count": 3,
        "outer_loop_count": 1,
        "inner_loop_count": 2,
        "message": "Created planar region with 2 inner loop(s)",
    }
    mock_get_connection.return_value = connection

    result = create_planar_region(
        ctx=None,
        outer_curve_id=OUTER,
        inner_curve_ids=[INNER_A, INNER_B],
        name="plate",
    )

    connection.send_command.assert_called_once_with(
        "create_planar_region",
        {
            "outer_curve_id": OUTER,
            "inner_curve_ids": [INNER_A, INNER_B],
            "name": "plate",
        },
    )
    assert result == {
        "success": True,
        "id": "region-id",
        "face_count": 1,
        "loop_count": 3,
        "outer_loop_count": 1,
        "inner_loop_count": 2,
        "message": "Created planar region with 2 inner loop(s)",
    }


@patch("rhinomcp.tools.create_planar_region.get_rhino_connection")
def test_defaults_inner_curves_to_empty_list_and_omits_name(mock_get_connection):
    connection = MagicMock()
    connection.send_command.return_value = {
        "id": "region-id",
        "face_count": 1,
        "loop_count": 1,
        "outer_loop_count": 1,
        "inner_loop_count": 0,
    }
    mock_get_connection.return_value = connection

    create_planar_region(ctx=None, outer_curve_id=OUTER)

    connection.send_command.assert_called_once_with(
        "create_planar_region",
        {"outer_curve_id": OUTER, "inner_curve_ids": []},
    )


@patch("rhinomcp.tools.create_planar_region.get_rhino_connection")
def test_transport_errors_remain_tool_errors(mock_get_connection):
    connection = MagicMock()
    connection.send_command.side_effect = RuntimeError("Rhino unavailable")
    mock_get_connection.return_value = connection

    with pytest.raises(RuntimeError, match="Rhino unavailable"):
        create_planar_region(ctx=None, outer_curve_id=OUTER)


def _validator():
    contracts = Path(__file__).parents[2] / "contracts"
    schema = json.loads(
        (contracts / "commands" / "create_planar_region.json").read_text()
    )
    return Draft202012Validator(
        schema,
        resolver=RefResolver(
            base_uri=(contracts / "commands").as_uri() + "/",
            referrer=schema,
        ),
    )


def test_schema_accepts_outer_only_and_multiple_distinct_holes():
    validator = _validator()
    assert not list(validator.iter_errors({"outer_curve_id": OUTER}))
    assert not list(
        validator.iter_errors(
            {
                "outer_curve_id": OUTER,
                "inner_curve_ids": [INNER_A, INNER_B],
                "name": "plate",
            }
        )
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"outer_curve_id": "not-a-guid"},
        {"outer_curve_id": OUTER, "inner_curve_ids": [INNER_A, INNER_A]},
        {"outer_curve_id": OUTER, "inner_curve_ids": ["not-a-guid"]},
        {"outer_curve_id": OUTER, "inner_curve_ids": None},
        {"outer_curve_id": OUTER, "delete_sources": True},
        {"outer_curve_id": OUTER, "unknown": 1},
    ],
)
def test_schema_rejects_invalid_or_unreviewed_parameters(payload):
    assert list(_validator().iter_errors(payload))
