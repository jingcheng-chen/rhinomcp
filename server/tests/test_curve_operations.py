"""
Unit tests for curve operations tools.
"""

from unittest.mock import patch, MagicMock
from rhinomcp.tools.curve_operations import project_curve, intersect_curves, split_curve



class TestProjectCurveTool:
    """Tests for project_curve tool."""

    @patch('rhinomcp.tools.curve_operations.get_rhino_connection')
    def test_project_curve_success(self, mock_get_conn):

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["proj-123"],
            "count": 1,
            "message": "Projected 1 curve(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = project_curve(
            ctx=None,
            curve_id="curve-123",
            target_ids=["surface-123"],
            direction=[0, 0, -1],
            name="test_proj"
        )

        assert result["success"] is True
        assert "result_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "project_curve"
        assert call_args[0][1]["curve_id"] == "curve-123"
        assert call_args[0][1]["target_ids"] == ["surface-123"]
        assert call_args[0][1]["direction"] == [0, 0, -1]

    def test_project_curve_invalid_direction(self):

        result = project_curve(
            ctx=None,
            curve_id="curve-123",
            target_ids=["surface-123"],
            direction=[0, 0]
        )

        assert result["success"] is False
        assert "direction" in result["message"].lower()

    def test_project_curve_no_targets(self):

        result = project_curve(
            ctx=None,
            curve_id="curve-123",
            target_ids=[],
            direction=[0, 0, -1]
        )

        assert result["success"] is False
        assert "target" in result["message"].lower()


class TestIntersectCurvesTool:
    """Tests for intersect_curves tool."""

    @patch('rhinomcp.tools.curve_operations.get_rhino_connection')
    def test_intersect_curves_success(self, mock_get_conn):

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "point_ids": ["pt-123"],
            "curve_ids": [],
            "points": [[10, 10, 0]],
            "message": "Found 1 intersection(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = intersect_curves(
            ctx=None,
            curve_id_a="curve-a",
            curve_id_b="curve-b",
            tolerance=0.1,
            name="test_int"
        )

        assert result["success"] is True
        assert "point_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "intersect_curves"
        assert call_args[0][1]["curve_id_a"] == "curve-a"
        assert call_args[0][1]["curve_id_b"] == "curve-b"
        assert call_args[0][1]["tolerance"] == 0.1


class TestSplitCurveTool:
    """Tests for split_curve tool."""

    @patch('rhinomcp.tools.curve_operations.get_rhino_connection')
    def test_split_curve_by_params(self, mock_get_conn):

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["seg-1", "seg-2"],
            "count": 2,
            "message": "Split curve into 2 segment(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = split_curve(
            ctx=None,
            curve_id="curve-123",
            parameters=[0.5],
            delete_source=True,
            name="split_segments"
        )

        assert result["success"] is True
        assert len(result["result_ids"]) == 2
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "split_curve"
        assert call_args[0][1]["curve_id"] == "curve-123"
        assert call_args[0][1]["parameters"] == [0.5]
        assert call_args[0][1]["delete_source"] is True

    @patch('rhinomcp.tools.curve_operations.get_rhino_connection')
    def test_split_curve_by_points(self, mock_get_conn):

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["seg-1", "seg-2"],
            "count": 2,
            "message": "Split curve into 2 segment(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = split_curve(
            ctx=None,
            curve_id="curve-123",
            point_ids=["pt-123"]
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["point_ids"] == ["pt-123"]

    def test_split_curve_no_params_or_points(self):

        result = split_curve(ctx=None, curve_id="curve-123")

        assert result["success"] is False
        assert "either parameters or point_ids" in result["message"].lower()
