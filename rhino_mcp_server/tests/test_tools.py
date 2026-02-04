"""
Unit tests for MCP tool functions.

These tests verify that MCP tool functions correctly:
1. Accept correct parameters
2. Call send_command with proper command type and params
3. Return properly formatted results

Uses mocking to avoid needing the actual Rhino connection.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCreateObjectTool:
    """Tests for create_object tool."""

    @patch('rhinomcp.tools.create_object.get_rhino_connection')
    def test_create_box(self, mock_get_conn):
        from rhinomcp.tools.create_object import create_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "TestBox",
            "type": "BOX"
        }
        mock_get_conn.return_value = mock_conn

        result = create_object(
            ctx=None,
            type="BOX",
            name="TestBox",
            params={"width": 1, "length": 1, "height": 1}
        )

        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "create_object"
        assert call_args[0][1]["type"] == "BOX"
        assert call_args[0][1]["name"] == "TestBox"
        assert "Created BOX object" in result

    @patch('rhinomcp.tools.create_object.get_rhino_connection')
    def test_create_sphere_with_color(self, mock_get_conn):
        from rhinomcp.tools.create_object import create_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "def-456",
            "name": "RedSphere",
            "type": "SPHERE"
        }
        mock_get_conn.return_value = mock_conn

        result = create_object(
            ctx=None,
            type="SPHERE",
            name="RedSphere",
            color=[255, 0, 0],
            params={"radius": 5}
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["color"] == [255, 0, 0]
        assert "RedSphere" in result

    @patch('rhinomcp.tools.create_object.get_rhino_connection')
    def test_create_with_transform(self, mock_get_conn):
        from rhinomcp.tools.create_object import create_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "ghi-789",
            "name": "TransformedBox",
            "type": "BOX"
        }
        mock_get_conn.return_value = mock_conn

        result = create_object(
            ctx=None,
            type="BOX",
            name="TransformedBox",
            params={"width": 1, "length": 1, "height": 1},
            translation=[10, 20, 30],
            rotation=[0.5, 0, 0],
            scale=[2, 2, 2]
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["translation"] == [10, 20, 30]
        assert call_args[0][1]["rotation"] == [0.5, 0, 0]
        assert call_args[0][1]["scale"] == [2, 2, 2]

    @patch('rhinomcp.tools.create_object.get_rhino_connection')
    def test_create_object_error(self, mock_get_conn):
        from rhinomcp.tools.create_object import create_object

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = Exception("Connection failed")
        mock_get_conn.return_value = mock_conn

        result = create_object(ctx=None, type="BOX", params={})
        assert "Error" in result


class TestCreateObjectsTool:
    """Tests for create_objects tool."""

    @patch('rhinomcp.tools.create_objects.get_rhino_connection')
    def test_create_multiple_objects(self, mock_get_conn):
        from rhinomcp.tools.create_objects import create_objects

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "objects": {
                "Box1": {"id": "id1", "name": "Box1"},
                "Box2": {"id": "id2", "name": "Box2"}
            },
            "success_count": 2,
            "failure_count": 0,
            "total": 2,
            "errors": []
        }
        mock_get_conn.return_value = mock_conn

        # create_objects takes a List of objects, not a Dict
        result = create_objects(
            ctx=None,
            objects=[
                {"type": "BOX", "name": "Box1", "params": {"width": 1, "length": 1, "height": 1}},
                {"type": "BOX", "name": "Box2", "params": {"width": 2, "length": 2, "height": 2}}
            ]
        )

        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "create_objects"
        assert "2" in result


class TestModifyObjectTool:
    """Tests for modify_object tool."""

    @patch('rhinomcp.tools.modify_object.get_rhino_connection')
    def test_modify_by_id(self, mock_get_conn):
        from rhinomcp.tools.modify_object import modify_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "NewName"
        }
        mock_get_conn.return_value = mock_conn

        result = modify_object(
            ctx=None,
            id="abc-123",
            new_name="NewName"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "modify_object"
        assert call_args[0][1]["id"] == "abc-123"
        assert call_args[0][1]["new_name"] == "NewName"

    @patch('rhinomcp.tools.modify_object.get_rhino_connection')
    def test_modify_color(self, mock_get_conn):
        from rhinomcp.tools.modify_object import modify_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "ColoredObject"
        }
        mock_get_conn.return_value = mock_conn

        result = modify_object(
            ctx=None,
            id="abc-123",
            new_color=[255, 128, 0]
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["new_color"] == [255, 128, 0]


class TestModifyObjectsTool:
    """Tests for modify_objects tool."""

    @patch('rhinomcp.tools.modify_objects.get_rhino_connection')
    def test_modify_multiple(self, mock_get_conn):
        from rhinomcp.tools.modify_objects import modify_objects

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success_count": 2,
            "failure_count": 0,
            "total": 2,
            "errors": []
        }
        mock_get_conn.return_value = mock_conn

        result = modify_objects(
            ctx=None,
            objects=[
                {"id": "id1", "new_name": "Name1"},
                {"id": "id2", "new_name": "Name2"}
            ]
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "modify_objects"
        assert "2" in result


class TestDeleteObjectTool:
    """Tests for delete_object tool."""

    @patch('rhinomcp.tools.delete_object.get_rhino_connection')
    def test_delete_by_id(self, mock_get_conn):
        from rhinomcp.tools.delete_object import delete_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "DeletedObject",
            "deleted": True
        }
        mock_get_conn.return_value = mock_conn

        result = delete_object(ctx=None, id="abc-123")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "delete_object"
        assert call_args[0][1]["id"] == "abc-123"

    @patch('rhinomcp.tools.delete_object.get_rhino_connection')
    def test_delete_all(self, mock_get_conn):
        from rhinomcp.tools.delete_object import delete_object

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "deleted": True,
            "count": 5
        }
        mock_get_conn.return_value = mock_conn

        result = delete_object(ctx=None, all=True)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1].get("all") is True


class TestGetObjectInfoTool:
    """Tests for get_object_info tool."""

    @patch('rhinomcp.tools.get_object_info.get_rhino_connection')
    def test_get_by_id(self, mock_get_conn):
        from rhinomcp.tools.get_object_info import get_object_info

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "TestObject",
            "type": "BOX"
        }
        mock_get_conn.return_value = mock_conn

        result = get_object_info(ctx=None, id="abc-123")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_object_info"
        assert call_args[0][1]["id"] == "abc-123"


class TestGetDocumentSummaryTool:
    """Tests for get_document_summary tool."""

    @patch('rhinomcp.tools.get_document_summary.get_rhino_connection')
    def test_get_document_summary(self, mock_get_conn):
        from rhinomcp.tools.get_document_summary import get_document_summary

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "meta_data": {"name": "test.3dm", "units": "Millimeters"},
            "object_count": 10,
            "objects_by_type": {"CURVE": 5, "BREP": 3, "POINT": 2},
            "objects_by_layer": {"Default": 10},
            "layer_count": 1,
            "layer_hierarchy": []
        }
        mock_get_conn.return_value = mock_conn

        result = get_document_summary(ctx=None)

        mock_conn.send_command.assert_called_once_with("get_document_summary")


class TestGetSelectedObjectsInfoTool:
    """Tests for get_selected_objects_info tool."""

    @patch('rhinomcp.tools.get_selected_objects_info.get_rhino_connection')
    def test_get_selected_objects_info(self, mock_get_conn):
        from rhinomcp.tools.get_selected_objects_info import get_selected_objects_info

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "selected_objects": [
                {"id": "1", "name": "Selected1"},
                {"id": "2", "name": "Selected2"}
            ]
        }
        mock_get_conn.return_value = mock_conn

        result = get_selected_objects_info(ctx=None, include_attributes=True)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_selected_objects_info"


class TestSelectObjectsTool:
    """Tests for select_objects tool."""

    @patch('rhinomcp.tools.select_objects.get_rhino_connection')
    def test_select_by_name(self, mock_get_conn):
        from rhinomcp.tools.select_objects import select_objects

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"count": 3}
        mock_get_conn.return_value = mock_conn

        result = select_objects(
            ctx=None,
            filters={"name": "TestObject"},
            filters_type="or"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "select_objects"
        assert call_args[0][1]["filters"]["name"] == "TestObject"


class TestCreateLayerTool:
    """Tests for create_layer tool."""

    @patch('rhinomcp.tools.create_layer.get_rhino_connection')
    def test_create_layer(self, mock_get_conn):
        from rhinomcp.tools.create_layer import create_layer

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "layer-123",
            "name": "NewLayer",
            "color": {"r": 255, "g": 0, "b": 0}
        }
        mock_get_conn.return_value = mock_conn

        result = create_layer(
            ctx=None,
            name="NewLayer",
            color=[255, 0, 0]
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "create_layer"
        assert call_args[0][1]["name"] == "NewLayer"
        assert call_args[0][1]["color"] == [255, 0, 0]


class TestDeleteLayerTool:
    """Tests for delete_layer tool."""

    @patch('rhinomcp.tools.delete_layer.get_rhino_connection')
    def test_delete_layer_by_name(self, mock_get_conn):
        from rhinomcp.tools.delete_layer import delete_layer

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "name": "DeletedLayer",
            "deleted": True
        }
        mock_get_conn.return_value = mock_conn

        result = delete_layer(ctx=None, name="DeletedLayer")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "delete_layer"
        assert call_args[0][1]["name"] == "DeletedLayer"


class TestGetOrSetCurrentLayerTool:
    """Tests for get_or_set_current_layer tool."""

    @patch('rhinomcp.tools.get_or_set_current_layer.get_rhino_connection')
    def test_set_current_layer(self, mock_get_conn):
        from rhinomcp.tools.get_or_set_current_layer import get_or_set_current_layer

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "layer-123",
            "name": "MyLayer"
        }
        mock_get_conn.return_value = mock_conn

        result = get_or_set_current_layer(ctx=None, name="MyLayer")

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_or_set_current_layer"
        assert call_args[0][1]["name"] == "MyLayer"

    @patch('rhinomcp.tools.get_or_set_current_layer.get_rhino_connection')
    def test_get_current_layer(self, mock_get_conn):
        from rhinomcp.tools.get_or_set_current_layer import get_or_set_current_layer

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "layer-123",
            "name": "CurrentLayer"
        }
        mock_get_conn.return_value = mock_conn

        result = get_or_set_current_layer(ctx=None)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_or_set_current_layer"


class TestBooleanOperationsTools:
    """Tests for boolean operation tools."""

    @patch('rhinomcp.tools.boolean_operations.get_rhino_connection')
    def test_boolean_union(self, mock_get_conn):
        from rhinomcp.tools.boolean_operations import boolean_union

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["result-123"],
            "count": 1,
            "message": "Boolean union created 1 object(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = boolean_union(
            ctx=None,
            object_ids=["id1", "id2"],
            delete_sources=True,
            name="UnionResult"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "boolean_union"
        assert call_args[0][1]["object_ids"] == ["id1", "id2"]
        assert call_args[0][1]["delete_sources"] is True
        assert call_args[0][1]["name"] == "UnionResult"
        assert "Boolean union created" in result

    @patch('rhinomcp.tools.boolean_operations.get_rhino_connection')
    def test_boolean_difference(self, mock_get_conn):
        from rhinomcp.tools.boolean_operations import boolean_difference

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["result-456"],
            "count": 1,
            "message": "Boolean difference created 1 object(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = boolean_difference(
            ctx=None,
            base_id="base-id",
            subtract_ids=["sub1", "sub2"],
            delete_sources=False,
            name="DiffResult"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "boolean_difference"
        assert call_args[0][1]["base_id"] == "base-id"
        assert call_args[0][1]["subtract_ids"] == ["sub1", "sub2"]
        assert call_args[0][1]["delete_sources"] is False
        assert "Boolean difference created" in result

    @patch('rhinomcp.tools.boolean_operations.get_rhino_connection')
    def test_boolean_intersection(self, mock_get_conn):
        from rhinomcp.tools.boolean_operations import boolean_intersection

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["result-789"],
            "count": 1,
            "message": "Boolean intersection created 1 object(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = boolean_intersection(
            ctx=None,
            object_ids=["id1", "id2", "id3"],
            delete_sources=True
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "boolean_intersection"
        assert call_args[0][1]["object_ids"] == ["id1", "id2", "id3"]
        assert "Boolean intersection created" in result


class TestUndoRedoTools:
    """Tests for undo and redo tools."""

    @patch('rhinomcp.tools.undo.get_rhino_connection')
    def test_undo_single(self, mock_get_conn):
        from rhinomcp.tools.undo import undo

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "undone_steps": 1,
            "requested_steps": 1,
            "message": "Undid 1 operation(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = undo(ctx=None, steps=1)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "undo"
        assert call_args[0][1]["steps"] == 1
        assert "Undid 1" in result

    @patch('rhinomcp.tools.undo.get_rhino_connection')
    def test_undo_multiple(self, mock_get_conn):
        from rhinomcp.tools.undo import undo

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "undone_steps": 3,
            "requested_steps": 3,
            "message": "Undid 3 operation(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = undo(ctx=None, steps=3)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["steps"] == 3

    @patch('rhinomcp.tools.undo.get_rhino_connection')
    def test_redo(self, mock_get_conn):
        from rhinomcp.tools.undo import redo

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "redone_steps": 1,
            "requested_steps": 1,
            "message": "Redid 1 operation(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = redo(ctx=None, steps=1)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "redo"
        assert call_args[0][1]["steps"] == 1
        assert "Redid 1" in result


class TestExecuteRhinoscriptTool:
    """Tests for execute_rhinoscript_python_code tool."""

    @patch('rhinomcp.tools.execute_rhinoscript_python_code.get_rhino_connection')
    def test_execute_script(self, mock_get_conn):
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": True,
            "result": "Script executed successfully"
        }
        mock_get_conn.return_value = mock_conn

        result = execute_rhinoscript_python_code(
            ctx=None,
            code="print('Hello')"
        )

        call_args = mock_conn.send_command.call_args
        # The command is "execute_rhinoscript_python_code"
        assert call_args[0][0] == "execute_rhinoscript_python_code"
        assert call_args[0][1]["code"] == "print('Hello')"

    @patch('rhinomcp.tools.execute_rhinoscript_python_code.get_rhino_connection')
    def test_execute_script_error(self, mock_get_conn):
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": False,
            "message": "Syntax error"
        }
        mock_get_conn.return_value = mock_conn

        result = execute_rhinoscript_python_code(
            ctx=None,
            code="invalid python code"
        )

        # Result is a Dict with the command response
        assert isinstance(result, dict)
        assert result.get("success") is False


class TestSearchRhinoscriptFunctionsTool:
    """Tests for search_rhinoscript_functions tool."""

    def test_search_functions(self):
        from rhinomcp.tools.rhinoscript_docs import search_rhinoscript_functions

        # This tool doesn't use the connection, it reads static data
        result = search_rhinoscript_functions(ctx=None, query="loft surface")

        # Should return a list of matching functions
        assert isinstance(result, list)
        assert len(result) > 0
        # Each result should have name, signature, description, module
        assert "name" in result[0]
        assert "signature" in result[0]

    def test_search_functions_with_limit(self):
        from rhinomcp.tools.rhinoscript_docs import search_rhinoscript_functions

        result = search_rhinoscript_functions(ctx=None, query="curve", limit=3)

        assert isinstance(result, list)
        assert len(result) <= 3


class TestGetRhinoscriptDocsTool:
    """Tests for get_rhinoscript_docs tool."""

    def test_get_docs(self):
        from rhinomcp.tools.rhinoscript_docs import get_rhinoscript_docs

        # This tool reads static data
        result = get_rhinoscript_docs(
            ctx=None,
            topic="add point"
        )

        # Should return a Dict with documentation
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert "documentation" in result
        assert len(result["documentation"]) > 0

    def test_get_docs_not_found(self):
        from rhinomcp.tools.rhinoscript_docs import get_rhinoscript_docs

        result = get_rhinoscript_docs(
            ctx=None,
            topic="xyznonexistentfunction123"
        )

        # Should return a Dict with success=False
        assert isinstance(result, dict)
        assert result.get("success") is False


class TestListRhinoscriptModulesTool:
    """Tests for list_rhinoscript_modules tool."""

    def test_list_modules(self):
        from rhinomcp.tools.rhinoscript_docs import list_rhinoscript_modules

        result = list_rhinoscript_modules(ctx=None)

        assert isinstance(result, dict)
        assert "modules" in result
        assert "total_modules" in result
        assert result["total_modules"] > 0


class TestGetModuleFunctionsTool:
    """Tests for get_module_functions tool."""

    def test_get_module_functions(self):
        from rhinomcp.tools.rhinoscript_docs import get_module_functions

        result = get_module_functions(ctx=None, module_name="curve")

        assert isinstance(result, dict)
        assert "functions" in result
        assert len(result["functions"]) > 0

    def test_get_module_functions_not_found(self):
        from rhinomcp.tools.rhinoscript_docs import get_module_functions

        result = get_module_functions(ctx=None, module_name="nonexistentmodule")

        assert isinstance(result, dict)
        assert "error" in result
