"""Transport behavior for optional planar end caps on single-rail sweeps."""

from unittest.mock import Mock, patch

import pytest

from rhinomcp.tools.advanced_geometry import sweep1


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"cap_planar_ends": False},
        {"cap_planar_ends": True, "closed": False},
        {"cap_planar_ends": True, "closed": True},
    ],
)
def test_sweep_cap_option_is_forwarded_independently_of_closed(options):
    connection = Mock()
    connection.send_command.return_value = {
        "result_ids": ["solid-id"],
        "message": "created",
    }
    with patch(
        "rhinomcp.tools.advanced_geometry.get_rhino_connection", return_value=connection
    ):
        result = sweep1(None, "rail-id", ["profile-id"], **options)
    assert result["success"] is True
    assert result["result_ids"] == ["solid-id"]
    connection.send_command.assert_called_once_with(
        "sweep1",
        {
            "rail_id": "rail-id",
            "profile_ids": ["profile-id"],
            "closed": options.get("closed", False),
            "cap_planar_ends": options.get("cap_planar_ends", False),
        },
    )


def test_sweep_cap_failure_is_reported_without_retry():
    connection = Mock()
    connection.send_command.side_effect = RuntimeError(
        "Sweep planar end capping failed"
    )
    with patch(
        "rhinomcp.tools.advanced_geometry.get_rhino_connection", return_value=connection
    ):
        result = sweep1(None, "rail-id", ["profile-id"], cap_planar_ends=True)
    assert result["success"] is False
    assert "capping failed" in result["message"]
    connection.send_command.assert_called_once()
