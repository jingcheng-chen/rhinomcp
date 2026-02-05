"""
Unit tests for Grasshopper MCP tool functions.

These tests verify that MCP tool functions correctly:
1. Accept correct parameters
2. Call send_command with proper command type and params
3. Return properly formatted results

Uses mocking to avoid needing the actual Grasshopper connection.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGetGHDocumentInfoTool:
    """Tests for get_gh_document_info tool."""

    @patch('grasshoppermcp.tools.get_document_info.get_grasshopper_connection')
    def test_get_document_info(self, mock_get_conn):
        from grasshoppermcp.tools.get_document_info import get_gh_document_info

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "has_document": True,
            "file_path": "/test/path.gh",
            "object_count": 5,
            "component_count": 3,
            "parameter_count": 2,
            "group_count": 0,
            "components_by_category": {"Params": 2, "Curve": 1}
        }
        mock_get_conn.return_value = mock_conn

        result = get_gh_document_info(ctx=None)

        mock_conn.send_command.assert_called_once_with("get_gh_document_info", {})
        assert result["has_document"] is True
        assert result["component_count"] == 3


class TestListComponentsTool:
    """Tests for list_components tool."""

    @patch('grasshoppermcp.tools.list_components.get_grasshopper_connection')
    def test_list_components_no_filter(self, mock_get_conn):
        from grasshoppermcp.tools.list_components import list_components

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "count": 2,
            "components": [
                {"instance_id": "id1", "name": "Circle", "nickname": "MyCircle"},
                {"instance_id": "id2", "name": "Point", "nickname": "MyPoint"}
            ]
        }
        mock_get_conn.return_value = mock_conn

        result = list_components(ctx=None)

        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "list_components"
        assert result["count"] == 2

    @patch('grasshoppermcp.tools.list_components.get_grasshopper_connection')
    def test_list_components_with_category_filter(self, mock_get_conn):
        from grasshoppermcp.tools.list_components import list_components

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "count": 1,
            "components": [
                {"instance_id": "id1", "name": "Circle", "category": "Curve"}
            ]
        }
        mock_get_conn.return_value = mock_conn

        result = list_components(ctx=None, category="Curve")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["category"] == "Curve"


class TestAddComponentTool:
    """Tests for add_component tool."""

    @patch('grasshoppermcp.tools.add_component.get_grasshopper_connection')
    def test_add_component(self, mock_get_conn):
        from grasshoppermcp.tools.add_component import add_component

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "instance_id": "new-guid-123",
            "name": "Circle",
            "nickname": "MyCircle",
            "category": "Curve",
            "position": [100, 50]
        }
        mock_get_conn.return_value = mock_conn

        result = add_component(
            ctx=None,
            component_name="Circle",
            position=[100, 50],
            nickname="MyCircle"
        )

        assert result["success"] is True
        assert result["instance_id"] == "new-guid-123"
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "add_component"
        assert call_args[0][1]["component_name"] == "Circle"
        assert call_args[0][1]["position"] == [100, 50]

    def test_add_component_empty_name(self):
        from grasshoppermcp.tools.add_component import add_component

        result = add_component(ctx=None, component_name="")

        assert result["success"] is False
        assert "required" in result["message"]


class TestDeleteComponentTool:
    """Tests for delete_component tool."""

    @patch('grasshoppermcp.tools.delete_component.get_grasshopper_connection')
    def test_delete_by_nickname(self, mock_get_conn):
        from grasshoppermcp.tools.delete_component import delete_component

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "deleted_id": "guid-123",
            "name": "Circle",
            "message": "Component deleted"
        }
        mock_get_conn.return_value = mock_conn

        result = delete_component(ctx=None, nickname="MyCircle")

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "delete_component"
        assert call_args[0][1]["nickname"] == "MyCircle"

    def test_delete_no_identifier(self):
        from grasshoppermcp.tools.delete_component import delete_component

        result = delete_component(ctx=None)

        assert result["success"] is False
        assert "required" in result["message"]


class TestGetComponentInfoTool:
    """Tests for get_component_info tool."""

    @patch('grasshoppermcp.tools.get_component_info.get_grasshopper_connection')
    def test_get_info_by_nickname(self, mock_get_conn):
        from grasshoppermcp.tools.get_component_info import get_component_info

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "instance_id": "guid-123",
            "name": "Circle",
            "nickname": "MyCircle",
            "inputs": [{"name": "Plane", "type": "Plane"}, {"name": "Radius", "type": "Number"}],
            "outputs": [{"name": "Circle", "type": "Curve"}],
            "runtime_message_level": "Blank"
        }
        mock_get_conn.return_value = mock_conn

        result = get_component_info(ctx=None, nickname="MyCircle")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_component_info"
        assert call_args[0][1]["nickname"] == "MyCircle"
        assert len(result["inputs"]) == 2

    def test_get_info_no_identifier(self):
        from grasshoppermcp.tools.get_component_info import get_component_info

        result = get_component_info(ctx=None)

        assert result["success"] is False


class TestConnectComponentsTool:
    """Tests for connect_components tool."""

    @patch('grasshoppermcp.tools.connect_components.get_grasshopper_connection')
    def test_connect_by_nickname(self, mock_get_conn):
        from grasshoppermcp.tools.connect_components import connect_components

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "source_id": "guid-1",
            "target_id": "guid-2",
            "source_param": "Circle",
            "target_param": "Profile",
            "message": "Connected successfully"
        }
        mock_get_conn.return_value = mock_conn

        result = connect_components(
            ctx=None,
            source_nickname="MyCircle",
            source_output=0,
            target_nickname="MyExtrude",
            target_input=0
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "connect_components"
        assert call_args[0][1]["source_nickname"] == "MyCircle"
        assert call_args[0][1]["target_nickname"] == "MyExtrude"

    def test_connect_missing_source(self):
        from grasshoppermcp.tools.connect_components import connect_components

        result = connect_components(
            ctx=None,
            target_nickname="MyExtrude"
        )

        assert result["success"] is False
        assert "source" in result["message"].lower()

    def test_connect_missing_target(self):
        from grasshoppermcp.tools.connect_components import connect_components

        result = connect_components(
            ctx=None,
            source_nickname="MyCircle"
        )

        assert result["success"] is False
        assert "target" in result["message"].lower()


class TestDisconnectComponentsTool:
    """Tests for disconnect_components tool."""

    @patch('grasshoppermcp.tools.disconnect_components.get_grasshopper_connection')
    def test_disconnect_by_nickname(self, mock_get_conn):
        from grasshoppermcp.tools.disconnect_components import disconnect_components

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "source_id": "guid-1",
            "target_id": "guid-2",
            "message": "Disconnected successfully"
        }
        mock_get_conn.return_value = mock_conn

        result = disconnect_components(
            ctx=None,
            source_nickname="MyCircle",
            source_output=0,
            target_nickname="MyExtrude",
            target_input=0
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "disconnect_components"


class TestSetParameterValueTool:
    """Tests for set_parameter_value tool."""

    @patch('grasshoppermcp.tools.set_parameter_value.get_grasshopper_connection')
    def test_set_numeric_value(self, mock_get_conn):
        from grasshoppermcp.tools.set_parameter_value import set_parameter_value

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "component_id": "guid-123",
            "input_name": "Value",
            "value": 42.5,
            "message": "Value set"
        }
        mock_get_conn.return_value = mock_conn

        result = set_parameter_value(
            ctx=None,
            nickname="MySlider",
            value=42.5
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "set_parameter_value"
        assert call_args[0][1]["value"] == 42.5

    @patch('grasshoppermcp.tools.set_parameter_value.get_grasshopper_connection')
    def test_set_value_by_input_name(self, mock_get_conn):
        from grasshoppermcp.tools.set_parameter_value import set_parameter_value

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "component_id": "guid-123",
            "input_name": "Radius",
            "value": 10.0,
            "message": "Value set"
        }
        mock_get_conn.return_value = mock_conn

        result = set_parameter_value(
            ctx=None,
            nickname="MyCircle",
            value=10.0,
            input_name="Radius"
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["input_name"] == "Radius"

    def test_set_value_no_identifier(self):
        from grasshoppermcp.tools.set_parameter_value import set_parameter_value

        result = set_parameter_value(ctx=None, value=42.5)

        assert result["success"] is False


class TestGetParameterValueTool:
    """Tests for get_parameter_value tool."""

    @patch('grasshoppermcp.tools.get_parameter_value.get_grasshopper_connection')
    def test_get_value(self, mock_get_conn):
        from grasshoppermcp.tools.get_parameter_value import get_parameter_value

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "component_id": "guid-123",
            "output_name": "Value",
            "value": 42.5,
            "data_type": "Number",
            "item_count": 1
        }
        mock_get_conn.return_value = mock_conn

        result = get_parameter_value(ctx=None, nickname="MySlider")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_parameter_value"
        assert result["value"] == 42.5

    def test_get_value_no_identifier(self):
        from grasshoppermcp.tools.get_parameter_value import get_parameter_value

        result = get_parameter_value(ctx=None)

        assert result["success"] is False


class TestRunSolutionTool:
    """Tests for run_solution tool."""

    @patch('grasshoppermcp.tools.run_solution.get_grasshopper_connection')
    def test_run_solution(self, mock_get_conn):
        from grasshoppermcp.tools.run_solution import run_solution

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "message": "Solution recomputed",
            "duration_ms": 150
        }
        mock_get_conn.return_value = mock_conn

        result = run_solution(ctx=None)

        assert result["success"] is True
        mock_conn.send_command.assert_called_once_with("run_solution", {})


class TestExpireSolutionTool:
    """Tests for expire_solution tool."""

    @patch('grasshoppermcp.tools.expire_solution.get_grasshopper_connection')
    def test_expire_entire_solution(self, mock_get_conn):
        from grasshoppermcp.tools.expire_solution import expire_solution

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "message": "Solution expired"
        }
        mock_get_conn.return_value = mock_conn

        result = expire_solution(ctx=None)

        assert result["success"] is True
        mock_conn.send_command.assert_called_once()

    @patch('grasshoppermcp.tools.expire_solution.get_grasshopper_connection')
    def test_expire_specific_component(self, mock_get_conn):
        from grasshoppermcp.tools.expire_solution import expire_solution

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "message": "Component expired",
            "expired_component": "guid-123"
        }
        mock_get_conn.return_value = mock_conn

        result = expire_solution(ctx=None, nickname="MyCircle")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["nickname"] == "MyCircle"


class TestBakeComponentTool:
    """Tests for bake_component tool."""

    @patch('grasshoppermcp.tools.bake_component.get_grasshopper_connection')
    def test_bake_by_nickname(self, mock_get_conn):
        from grasshoppermcp.tools.bake_component import bake_component

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "baked_count": 1,
            "object_ids": ["rhino-guid-1"],
            "layer": "Default",
            "message": "Baked 1 objects"
        }
        mock_get_conn.return_value = mock_conn

        result = bake_component(ctx=None, nickname="MyCircle")

        assert result["success"] is True
        assert result["baked_count"] == 1
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "bake_component"

    @patch('grasshoppermcp.tools.bake_component.get_grasshopper_connection')
    def test_bake_with_layer(self, mock_get_conn):
        from grasshoppermcp.tools.bake_component import bake_component

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "baked_count": 1,
            "object_ids": ["rhino-guid-1"],
            "layer": "GH Output",
            "message": "Baked 1 objects"
        }
        mock_get_conn.return_value = mock_conn

        result = bake_component(
            ctx=None,
            nickname="MyCircle",
            layer_name="GH Output"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["layer_name"] == "GH Output"

    def test_bake_no_identifier(self):
        from grasshoppermcp.tools.bake_component import bake_component

        result = bake_component(ctx=None)

        assert result["success"] is False


class TestGetCanvasStateTool:
    """Tests for get_canvas_state tool."""

    @patch('grasshoppermcp.tools.get_canvas_state.get_grasshopper_connection')
    def test_get_canvas_state(self, mock_get_conn):
        from grasshoppermcp.tools.get_canvas_state import get_canvas_state

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "component_count": 3,
            "connection_count": 2,
            "components": [
                {"instance_id": "id1", "name": "Point"},
                {"instance_id": "id2", "name": "Circle"},
                {"instance_id": "id3", "name": "Extrude"}
            ],
            "connections": [
                {"source_id": "id1", "target_id": "id2"},
                {"source_id": "id2", "target_id": "id3"}
            ],
            "groups": []
        }
        mock_get_conn.return_value = mock_conn

        result = get_canvas_state(ctx=None)

        mock_conn.send_command.assert_called_once_with("get_canvas_state", {})
        assert result["component_count"] == 3
        assert result["connection_count"] == 2
        assert len(result["components"]) == 3


class TestConnectionErrors:
    """Tests for error handling when connection fails."""

    @patch('grasshoppermcp.tools.add_component.get_grasshopper_connection')
    def test_add_component_connection_error(self, mock_get_conn):
        from grasshoppermcp.tools.add_component import add_component

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = Exception("Connection failed")
        mock_get_conn.return_value = mock_conn

        result = add_component(ctx=None, component_name="Circle")

        assert result["success"] is False
        assert "Connection failed" in result["message"]

    @patch('grasshoppermcp.tools.bake_component.get_grasshopper_connection')
    def test_bake_component_connection_error(self, mock_get_conn):
        from grasshoppermcp.tools.bake_component import bake_component

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = Exception("Timeout")
        mock_get_conn.return_value = mock_conn

        result = bake_component(ctx=None, nickname="MyCircle")

        assert result["success"] is False
        assert "Timeout" in result["message"]
