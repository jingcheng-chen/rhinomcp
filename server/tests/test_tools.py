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
        # Structured return: callers need the id for follow-up calls.
        assert result["success"] is True
        assert result["id"] == "abc-123"
        assert result["type"] == "BOX"
        assert "Created BOX object" in result["message"]

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
        assert result["name"] == "RedSphere"

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
    def test_create_object_error_propagates(self, mock_get_conn):
        """Connection failures should surface as exceptions, not "Error ..." strings —
        otherwise MCP clients see a successful tool call with an error message."""
        from rhinomcp.tools.create_object import create_object

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = Exception("Connection failed")
        mock_get_conn.return_value = mock_conn

        with pytest.raises(Exception, match="Connection failed"):
            create_object(ctx=None, type="BOX", params={"width": 1, "length": 1, "height": 1})


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


class TestObjectAttributesTools:
    """Tests for object attribute read/update tools."""

    @patch('rhinomcp.tools.object_attributes.get_rhino_connection')
    def test_get_object_attributes_by_id(self, mock_get_conn):
        from rhinomcp.tools.object_attributes import get_object_attributes

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "Box1",
            "user_strings": {"PartNo": "A-100"}
        }
        mock_get_conn.return_value = mock_conn

        result = get_object_attributes(ctx=None, id="abc-123")

        mock_conn.send_command.assert_called_once_with("get_object_attributes", {"id": "abc-123"})
        assert result["user_strings"]["PartNo"] == "A-100"

    @patch('rhinomcp.tools.object_attributes.get_rhino_connection')
    def test_update_object_attributes(self, mock_get_conn):
        from rhinomcp.tools.object_attributes import update_object_attributes

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "id": "abc-123",
            "name": "Panel",
            "layer": {"name": "Parts"},
            "visible": True,
            "locked": False,
            "user_strings": {"PartNo": "A-100", "Count": "3"}
        }
        mock_get_conn.return_value = mock_conn

        result = update_object_attributes(
            ctx=None,
            id="abc-123",
            new_name="Panel",
            layer="Parts",
            color=[10, 20, 30],
            user_strings={"PartNo": "A-100", "Count": 3},
            delete_user_strings=["OldKey"],
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "update_object_attributes"
        assert call_args[0][1]["id"] == "abc-123"
        assert call_args[0][1]["new_name"] == "Panel"
        assert call_args[0][1]["layer"] == "Parts"
        assert call_args[0][1]["color"] == [10, 20, 30]
        assert call_args[0][1]["user_strings"]["Count"] == 3
        assert call_args[0][1]["delete_user_strings"] == ["OldKey"]
        assert result["user_strings"]["Count"] == "3"

    @patch('rhinomcp.tools.object_attributes.get_rhino_connection')
    def test_update_object_attributes_rejects_noop(self, mock_get_conn):
        from rhinomcp.tools.object_attributes import update_object_attributes

        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError, match="at least one attribute update"):
            update_object_attributes(ctx=None, id="abc-123")

        mock_conn.send_command.assert_not_called()

    @patch('rhinomcp.tools.object_attributes.get_rhino_connection')
    def test_update_object_attributes_rejects_nested_user_strings(self, mock_get_conn):
        from rhinomcp.tools.object_attributes import update_object_attributes

        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError, match="User string values"):
            update_object_attributes(ctx=None, id="abc-123", user_strings={"nested": {"bad": True}})

        mock_conn.send_command.assert_not_called()


class TestAnalyzeObjectsTool:
    """Tests for analyze_objects tool."""

    @patch('rhinomcp.tools.analyze_objects.get_rhino_connection')
    def test_analyze_object_by_id(self, mock_get_conn):
        from rhinomcp.tools.analyze_objects import analyze_objects

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "object_count": 1,
            "analyses": [
                {
                    "id": "abc-123",
                    "name": "Line1",
                    "type": "LINE",
                    "valid": True,
                    "metrics": {"length": 10},
                }
            ],
        }
        mock_get_conn.return_value = mock_conn

        result = analyze_objects(ctx=None, id="abc-123")

        mock_conn.send_command.assert_called_once_with("analyze_objects", {"id": "abc-123"})
        assert result["object_count"] == 1
        assert result["analyses"][0]["metrics"]["length"] == 10

    @patch('rhinomcp.tools.analyze_objects.get_rhino_connection')
    def test_analyze_objects_by_ids(self, mock_get_conn):
        from rhinomcp.tools.analyze_objects import analyze_objects

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"object_count": 2, "analyses": []}
        mock_get_conn.return_value = mock_conn

        analyze_objects(ctx=None, object_ids=["id-1", "id-2"])

        mock_conn.send_command.assert_called_once_with("analyze_objects", {"object_ids": ["id-1", "id-2"]})

    @patch('rhinomcp.tools.analyze_objects.get_rhino_connection')
    def test_analyze_objects_rejects_mixed_selectors(self, mock_get_conn):
        from rhinomcp.tools.analyze_objects import analyze_objects

        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError, match="exactly one"):
            analyze_objects(ctx=None, id="abc-123", selected=True)

        mock_conn.send_command.assert_not_called()

    @patch('rhinomcp.tools.analyze_objects.get_rhino_connection')
    def test_analyze_objects_rejects_empty_object_ids(self, mock_get_conn):
        from rhinomcp.tools.analyze_objects import analyze_objects

        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError, match="at least one id"):
            analyze_objects(ctx=None, object_ids=[])

        mock_conn.send_command.assert_not_called()


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
            "count": 5,
            "scope": "all"
        }
        mock_get_conn.return_value = mock_conn

        result = delete_object(ctx=None, all=True)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1].get("all") is True
        # Wrapper must not crash on the all=true response (no "name" key) and must report count.
        assert result["success"] is True
        assert result["count"] == 5
        assert result["scope"] == "all"

    def test_delete_no_selector_raises(self):
        from rhinomcp.tools.delete_object import delete_object

        with pytest.raises(ValueError, match="must specify"):
            delete_object(ctx=None)

    def test_delete_mixed_selector_raises(self):
        """Mixed selectors (e.g. id + all=True) must be rejected before dispatch —
        otherwise C# prioritizes all and silently wipes the document."""
        from rhinomcp.tools.delete_object import delete_object

        with pytest.raises(ValueError, match="exactly one"):
            delete_object(ctx=None, id="abc-123", all=True)


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
            filters={"name": ["TestObject"]},
            filters_type="or"
        )

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "select_objects"
        assert call_args[0][1]["filters"]["name"] == ["TestObject"]


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

    @patch('rhinomcp.tools.execute_rhinoscript_python_code.get_rhino_connection')
    def test_execute_script_success_returns_output(self, mock_get_conn):
        """Successful execution surfaces captured output (Python print + Rhino lines)."""
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": True,
            "output": "Hello from print()\nRhino: Box created."
        }
        mock_get_conn.return_value = mock_conn

        result = execute_rhinoscript_python_code(ctx=None, code="print('Hello from print()')")
        assert result["success"] is True
        assert "Hello from print()" in result["output"]
        assert "Rhino: Box created." in result["output"]

    @patch('rhinomcp.tools.execute_rhinoscript_python_code.get_rhino_connection')
    def test_execute_script_failure_preserves_partial_output(self, mock_get_conn):
        """When the script raises, captured output up to the exception is preserved."""
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": False,
            "output": "Step 1 done\nStep 2 done\n",
            "message": "ZeroDivisionError: division by zero"
        }
        mock_get_conn.return_value = mock_conn

        result = execute_rhinoscript_python_code(ctx=None, code="raise ZeroDivisionError()")
        assert result["success"] is False
        # Partial output must survive — that's the whole point of the slice.
        assert "Step 1 done" in result["output"]
        assert "Step 2 done" in result["output"]
        assert "ZeroDivisionError" in result["message"]

    @patch('rhinomcp.tools.execute_rhinoscript_python_code.get_rhino_connection')
    def test_execute_script_failure_without_exception_has_message(self, mock_get_conn):
        """ExecuteScript may return false without throwing; a message must still be set."""
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": False,
            "output": "",
            "message": "Script execution returned false (no exception raised)."
        }
        mock_get_conn.return_value = mock_conn

        result = execute_rhinoscript_python_code(ctx=None, code="# triggers ExecuteScript false")
        assert result["success"] is False
        assert result.get("message"), "failure response must include a non-empty message"
        assert "returned false" in result["message"]


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


# =============================================================================
# Advanced Geometry Tools Tests
# =============================================================================

class TestLoftTool:
    """Tests for loft tool."""

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_loft_success(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import loft

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["guid-1", "guid-2"],
            "count": 2,
            "message": "Loft created 2 surface(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = loft(
            ctx=None,
            curve_ids=["curve-1", "curve-2", "curve-3"],
            name="test_loft",
            closed=False,
            loft_type=0
        )

        assert result["success"] is True
        assert "result_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "loft"
        assert call_args[0][1]["curve_ids"] == ["curve-1", "curve-2", "curve-3"]

    def test_loft_insufficient_curves(self):
        from rhinomcp.tools.advanced_geometry import loft

        result = loft(ctx=None, curve_ids=["only-one"])

        assert result["success"] is False
        assert "at least 2 curves" in result["message"]


class TestExtrudeCurveTool:
    """Tests for extrude_curve tool."""

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_extrude_curve_success(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import extrude_curve

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_id": "extruded-guid",
            "message": "Extrusion created successfully"
        }
        mock_get_conn.return_value = mock_conn

        result = extrude_curve(
            ctx=None,
            curve_id="curve-guid",
            direction=[0, 0, 10],
            name="test_extrusion",
            cap=True
        )

        assert result["success"] is True
        assert result["result_id"] == "extruded-guid"
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "extrude_curve"
        assert call_args[0][1]["direction"] == [0, 0, 10]

    def test_extrude_curve_invalid_direction(self):
        from rhinomcp.tools.advanced_geometry import extrude_curve

        result = extrude_curve(ctx=None, curve_id="curve-guid", direction=[0, 0])

        assert result["success"] is False
        assert "direction" in result["message"].lower()


class TestSweep1Tool:
    """Tests for sweep1 tool."""

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_sweep1_success(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import sweep1

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["swept-guid"],
            "count": 1,
            "message": "Sweep created 1 surface(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = sweep1(
            ctx=None,
            rail_id="rail-guid",
            profile_ids=["profile-1", "profile-2"],
            name="test_sweep"
        )

        assert result["success"] is True
        assert "result_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "sweep1"
        assert call_args[0][1]["rail_id"] == "rail-guid"

    def test_sweep1_no_profiles(self):
        from rhinomcp.tools.advanced_geometry import sweep1

        result = sweep1(ctx=None, rail_id="rail-guid", profile_ids=[])

        assert result["success"] is False
        assert "profile" in result["message"].lower()


class TestOffsetCurveTool:
    """Tests for offset_curve tool."""

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_offset_curve_success(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import offset_curve

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["offset-guid"],
            "count": 1,
            "message": "Offset created 1 curve(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = offset_curve(
            ctx=None,
            curve_id="curve-guid",
            distance=2.5,
            name="test_offset"
        )

        assert result["success"] is True
        assert "result_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "offset_curve"
        assert call_args[0][1]["distance"] == 2.5

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_offset_curve_with_plane(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import offset_curve

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["offset-guid"],
            "count": 1,
            "message": "Offset created 1 curve(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = offset_curve(
            ctx=None,
            curve_id="curve-guid",
            distance=1.0,
            plane=[0, 0, 1]
        )

        assert result["success"] is True
        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["plane"] == [0, 0, 1]


class TestPipeTool:
    """Tests for pipe tool."""

    @patch('rhinomcp.tools.advanced_geometry.get_rhino_connection')
    def test_pipe_success(self, mock_get_conn):
        from rhinomcp.tools.advanced_geometry import pipe

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "result_ids": ["pipe-guid"],
            "count": 1,
            "message": "Pipe created 1 object(s)"
        }
        mock_get_conn.return_value = mock_conn

        result = pipe(
            ctx=None,
            curve_id="curve-guid",
            radius=0.5,
            name="test_pipe",
            cap=True
        )

        assert result["success"] is True
        assert "result_ids" in result
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "pipe"
        assert call_args[0][1]["radius"] == 0.5

    def test_pipe_invalid_radius(self):
        from rhinomcp.tools.advanced_geometry import pipe

        result = pipe(ctx=None, curve_id="curve-guid", radius=0)

        assert result["success"] is False
        assert "radius" in result["message"].lower()

    def test_pipe_negative_radius(self):
        from rhinomcp.tools.advanced_geometry import pipe

        result = pipe(ctx=None, curve_id="curve-guid", radius=-1.0)

        assert result["success"] is False
        assert "radius" in result["message"].lower()


class TestRunCommandTool:
    """Tests for run_command tool (Rhino command escape hatch)."""

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_returns_output(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": True,
            "command": "_Box 0,0,0 10,10,10",
            "output": "Box command completed."
        }
        mock_get_conn.return_value = mock_conn

        result = run_command(ctx=None, command="_Box 0,0,0 10,10,10")

        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "run_command"
        assert call_args[0][1]["command"] == "_Box 0,0,0 10,10,10"
        assert call_args[0][1]["echo"] is False
        assert "Box command completed" in result

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_passes_echo_flag(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True, "command": "_Box", "output": ""}
        mock_get_conn.return_value = mock_conn

        run_command(ctx=None, command="_Box", echo=True)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["echo"] is True

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_empty_output_returns_done(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True, "command": "_NoOp", "output": ""}
        mock_get_conn.return_value = mock_conn

        result = run_command(ctx=None, command="_NoOp")
        assert result == "Done."

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_handles_connection_error(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_get_conn.side_effect = Exception("Connection refused")

        result = run_command(ctx=None, command="_Box")
        assert "Error running Rhino command" in result
        assert "Connection refused" in result

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_failure_is_flagged(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": False,
            "command": "_NotARealCommand",
            "output": "Unknown command: _NotARealCommand"
        }
        mock_get_conn.return_value = mock_conn

        result = run_command(ctx=None, command="_NotARealCommand")
        assert result.startswith("Command failed:")
        assert "Unknown command" in result

    @patch('rhinomcp.tools.run_command.get_rhino_connection')
    def test_run_command_failure_no_output(self, mock_get_conn):
        from rhinomcp.tools.run_command import run_command

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": False,
            "command": "_X",
            "output": ""
        }
        mock_get_conn.return_value = mock_conn

        result = run_command(ctx=None, command="_X")
        assert result.startswith("Command failed:")


class TestGetCommandsTool:
    """Tests for get_commands tool (Rhino command discovery)."""

    @patch('rhinomcp.tools.get_commands.get_rhino_connection')
    def test_get_commands_no_filter(self, mock_get_conn):
        from rhinomcp.tools.get_commands import get_commands

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "count": 3,
            "commands": ["Box", "Circle", "Sphere"]
        }
        mock_get_conn.return_value = mock_conn

        result = get_commands(ctx=None)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "get_commands"
        assert call_args[0][1]["filter"] == ""
        assert call_args[0][1]["loaded_only"] is True
        assert "Box" in result
        assert "Sphere" in result

    @patch('rhinomcp.tools.get_commands.get_rhino_connection')
    def test_get_commands_with_filter(self, mock_get_conn):
        from rhinomcp.tools.get_commands import get_commands

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "count": 2,
            "commands": ["BooleanDifference", "BooleanUnion"]
        }
        mock_get_conn.return_value = mock_conn

        get_commands(ctx=None, filter="boolean", loaded_only=False)

        call_args = mock_conn.send_command.call_args
        assert call_args[0][1]["filter"] == "boolean"
        assert call_args[0][1]["loaded_only"] is False


class TestExecutionSafetyGates:
    """The arbitrary-code execution tools must refuse calls when their
    env flag is off, before reaching Rhino."""

    @patch.dict("os.environ", {"RHINO_MCP_ENABLE_RUN_COMMAND": "0"})
    def test_run_command_disabled(self):
        from rhinomcp.tools.run_command import run_command
        result = run_command(ctx=None, command="_Box")
        assert "disabled" in result.lower()
        assert "RHINO_MCP_ENABLE_RUN_COMMAND" in result

    @patch.dict("os.environ", {"RHINO_MCP_ENABLE_RHINOSCRIPT": "0"})
    def test_rhinoscript_disabled(self):
        from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code
        result = execute_rhinoscript_python_code(ctx=None, code="print('x')")
        assert result["success"] is False
        assert "disabled" in result["message"].lower()
        assert "RHINO_MCP_ENABLE_RHINOSCRIPT" in result["message"]

    @patch.dict("os.environ", {"RHINO_MCP_ENABLE_CSHARP": "0"})
    def test_csharp_disabled(self):
        from rhinomcp.tools.execute_rhinocommon_csharp_code import execute_rhinocommon_csharp_code
        result = execute_rhinocommon_csharp_code(ctx=None, code="// noop")
        assert result["success"] is False
        assert "disabled" in result["message"].lower()
        assert "RHINO_MCP_ENABLE_CSHARP" in result["message"]


class TestGrasshopperTools:
    """Tests for Grasshopper MCP wrappers."""

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_document_setup_tool(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_document import gh_create_document

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_create_document(ctx=None, new_if_missing=True, make_active=False, open_canvas=True)

        mock_conn.send_command.assert_called_once_with(
            "gh_create_document",
            {
                "new_if_missing": True,
                "make_active": False,
                "open_canvas": True,
            },
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_readonly_discovery_tools(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_catalog import (
            gh_batch_get_component_type_info,
            gh_batch_search_components,
            gh_get_available_components,
            gh_get_component_type_info,
            gh_list_component_categories,
            gh_search_components,
        )
        from rhinomcp.tools.grasshopper_components import gh_get_component_info, gh_list_components
        from rhinomcp.tools.grasshopper_document import gh_get_canvas_state, gh_get_document_info
        from rhinomcp.tools.grasshopper_graph import gh_get_graph

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_get_document_info(ctx=None)
        gh_search_components(ctx=None, query="add", category="Maths", limit=5)
        gh_batch_search_components(ctx=None, queries=["Circle", "Panel"], max_matches=8)
        gh_list_component_categories(ctx=None)
        gh_get_available_components(ctx=None, category="Curve", include_description=True, limit=25)
        gh_get_component_type_info(ctx=None, name="Circle")
        gh_batch_get_component_type_info(
            ctx=None,
            components=[{"name": "Circle"}, {"guid": "12345678-1234-1234-1234-123456789012"}],
        )
        gh_list_components(ctx=None, category="Curve", name="Circle", limit=10)
        gh_get_component_info(ctx=None, instance_id="abc")
        gh_get_canvas_state(ctx=None, include_connections=False, include_values=True, max_items=3)
        gh_get_graph(ctx=None, graph_id="TestGraph", include_values=True, max_items=5)

        calls = mock_conn.send_command.call_args_list
        assert calls[0][0] == ("gh_get_document_info", {})
        assert calls[1][0] == ("gh_search_components", {"limit": 5, "query": "add", "category": "Maths"})
        assert calls[2][0] == (
            "gh_batch_search_components",
            {"queries": ["Circle", "Panel"], "max_matches": 8},
        )
        assert calls[3][0] == ("gh_list_component_categories", {})
        assert calls[4][0] == (
            "gh_get_available_components",
            {"include_description": True, "limit": 25, "category": "Curve"},
        )
        assert calls[5][0] == ("gh_get_component_type_info", {"name": "Circle"})
        assert calls[6][0] == (
            "gh_batch_get_component_type_info",
            {"components": [{"name": "Circle"}, {"guid": "12345678-1234-1234-1234-123456789012"}]},
        )
        assert calls[7][0] == ("gh_list_components", {"limit": 10, "category": "Curve", "name": "Circle"})
        assert calls[8][0] == ("gh_get_component_info", {"instance_id": "abc"})
        assert calls[9][0] == (
            "gh_get_canvas_state",
            {"include_connections": False, "include_values": True, "max_items": 3},
        )
        assert calls[10][0] == (
            "gh_get_graph",
            {"graph_id": "TestGraph", "include_values": True, "max_items": 5},
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_solution_tools(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_solution import gh_expire_solution, gh_run_solution

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_run_solution(ctx=None, expire_all=True)
        gh_expire_solution(
            ctx=None,
            nickname="Circle",
            component_ids=["abc"],
            expire_downstream=False,
            recompute=True,
        )

        calls = mock_conn.send_command.call_args_list
        assert calls[0][0] == ("gh_run_solution", {"expire_all": True})
        assert calls[1][0] == (
            "gh_expire_solution",
            {
                "expire_downstream": False,
                "recompute": True,
                "nickname": "Circle",
                "component_ids": ["abc"],
            },
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_build_graph_tool(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_build import gh_build_graph

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_build_graph(
            ctx=None,
            components=[
                {
                    "alias": "slider_a",
                    "component_name": "Number Slider",
                    "nickname": "A",
                    "value": 3.5,
                    "min": 0,
                    "max": 10,
                    "decimals": 2,
                },
                {"alias": "add", "component_name": "Addition", "nickname": "Add"},
            ],
            connections=[
                {
                    "source": "slider_a",
                    "target": "add",
                    "target_input_index": 0,
                }
            ],
            values=[
                {
                    "target": "slider_a",
                    "value": 4.0,
                    "decimals": 1,
                }
            ],
            preview_updates={"enabled": False},
            layout={"enabled": True, "start_position": [40, 40], "max_columns": 6},
            recompute=False,
            rollback_on_error=True,
        )

        mock_conn.send_command.assert_called_once_with(
            "gh_build_graph",
            {
                "components": [
                    {
                        "alias": "slider_a",
                        "component_name": "Number Slider",
                        "nickname": "A",
                        "value": 3.5,
                        "min": 0,
                        "max": 10,
                        "decimals": 2,
                    },
                    {"alias": "add", "component_name": "Addition", "nickname": "Add"},
                ],
                "connections": [
                    {
                        "source": "slider_a",
                        "target": "add",
                        "target_input_index": 0,
                    }
                ],
                "values": [
                    {
                        "target": "slider_a",
                        "value": 4.0,
                        "decimals": 1,
                    }
                ],
                "preview_updates": {"enabled": False},
                "layout": {"enabled": True, "start_position": [40, 40], "max_columns": 6},
                "recompute": False,
                "rollback_on_error": True,
                "open_canvas": True,
            },
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_mutate_graph_tool(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_mutation import gh_mutate_graph

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_mutate_graph(
            ctx=None,
            graph_id="PointAttractor_20260604",
            operations=[
                {
                    "op": "create",
                    "alias": "height",
                    "component_name": "Number Slider",
                    "value": 8,
                    "min": 0,
                    "max": 20,
                    "role": "control",
                },
                {
                    "op": "update",
                    "target": "cylinder",
                    "preview": False,
                },
                {
                    "op": "connect",
                    "source": "height",
                    "target": "cap",
                    "target_input_index": 0,
                },
            ],
            preview_policy={"mode": "only", "targets": ["cap"]},
            groups=[{"name": "Output", "targets": ["cap"], "color": [180, 220, 255]}],
            layout={"enabled": True, "targets": ["height", "cap"], "max_columns": 6},
            verify={
                "run_solution": True,
                "outputs": [
                    {
                        "target": "cap",
                        "output_index": 0,
                        "expect_count_min": 1,
                        "expect_type": "Brep",
                    }
                ],
            },
            fail_on_verification_error=True,
            recompute=True,
            rollback_on_error=True,
        )

        mock_conn.send_command.assert_called_once_with(
            "gh_mutate_graph",
            {
                "operations": [
                    {
                        "op": "create",
                        "alias": "height",
                        "component_name": "Number Slider",
                        "value": 8,
                        "min": 0,
                        "max": 20,
                        "role": "control",
                    },
                    {
                        "op": "update",
                        "target": "cylinder",
                        "preview": False,
                    },
                    {
                        "op": "connect",
                        "source": "height",
                        "target": "cap",
                        "target_input_index": 0,
                    },
                ],
                "fail_on_verification_error": True,
                "recompute": True,
                "rollback_on_error": True,
                "open_canvas": True,
                "graph_id": "PointAttractor_20260604",
                "preview_policy": {"mode": "only", "targets": ["cap"]},
                "groups": [{"name": "Output", "targets": ["cap"], "color": [180, 220, 255]}],
                "layout": {"enabled": True, "targets": ["height", "cap"], "max_columns": 6},
                "verify": {
                    "run_solution": True,
                    "outputs": [
                        {
                            "target": "cap",
                            "output_index": 0,
                            "expect_count_min": 1,
                            "expect_type": "Brep",
                        }
                    ],
                },
            },
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_component_lifecycle_tools(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_components import (
            gh_add_component,
            gh_clear_canvas,
            gh_delete_component,
            gh_layout_components,
            gh_update_component,
        )
        from rhinomcp.tools.grasshopper_graph import gh_clear_graph

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_add_component(
            ctx=None,
            component_name="Number Slider",
            position=[10, 20],
            nickname="Radius",
            value=5,
            min=0,
            max=10,
            decimals=1,
        )
        gh_add_component(ctx=None, component_guid="12345678-1234-1234-1234-123456789012")
        gh_add_component(ctx=None, component_name="Panel", nickname="AutoPlaced")
        gh_update_component(
            ctx=None,
            instance_id="abc",
            new_nickname="Radius2",
            position=[30, 40],
            enabled=False,
            preview=False,
        )
        gh_layout_components(
            ctx=None,
            component_ids=["abc", "def"],
            start_position=[20, 30],
            x_spacing=200,
            y_spacing=75,
            recompute=True,
        )
        gh_delete_component(ctx=None, nickname="Radius2")
        gh_clear_canvas(ctx=None, include_groups=False, recompute=True)
        gh_clear_graph(ctx=None, graph_id="TestGraph", include_groups=False, recompute=True)

        calls = mock_conn.send_command.call_args_list
        assert calls[0][0] == (
            "gh_add_component",
            {
                "position": [10, 20],
                "component_name": "Number Slider",
                "nickname": "Radius",
                "value": 5,
                "min": 0,
                "max": 10,
                "decimals": 1,
            },
        )
        assert calls[1][0] == (
            "gh_add_component",
            {
                "component_guid": "12345678-1234-1234-1234-123456789012",
            },
        )
        assert calls[2][0] == (
            "gh_add_component",
            {
                "component_name": "Panel",
                "nickname": "AutoPlaced",
            },
        )
        assert calls[3][0] == (
            "gh_update_component",
            {
                "instance_id": "abc",
                "new_nickname": "Radius2",
                "position": [30, 40],
                "enabled": False,
                "preview": False,
            },
        )
        assert calls[4][0] == (
            "gh_layout_components",
            {
                "include_groups": False,
                "x_spacing": 200,
                "y_spacing": 75,
                "recompute": True,
                "component_ids": ["abc", "def"],
                "start_position": [20, 30],
            },
        )
        assert calls[5][0] == ("gh_delete_component", {"nickname": "Radius2"})
        assert calls[6][0] == ("gh_clear_canvas", {"include_groups": False, "recompute": True})
        assert calls[7][0] == (
            "gh_clear_graph",
            {"graph_id": "TestGraph", "include_groups": False, "recompute": True},
        )

    @patch("rhinomcp.tools._grasshopper_common.get_rhino_connection")
    def test_gh_connection_and_parameter_tools(self, mock_get_conn):
        from rhinomcp.tools.grasshopper_connections import (
            gh_connect_components,
            gh_disconnect_components,
        )
        from rhinomcp.tools.grasshopper_parameters import (
            gh_get_parameter_value,
            gh_set_parameter_value,
        )

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"success": True}
        mock_get_conn.return_value = mock_conn

        gh_connect_components(
            ctx=None,
            source_instance_id="src",
            source_output_index=0,
            target_nickname="Circle",
            target_input_name="Radius",
        )
        gh_disconnect_components(ctx=None, target_instance_id="dst", disconnect_all=True)
        gh_set_parameter_value(
            ctx=None,
            nickname="Radius",
            value=7.5,
            input_name="R",
            min=0,
            max=10,
            decimals=2,
        )
        gh_get_parameter_value(ctx=None, instance_id="circle-id", output_name="C", max_items=12)

        calls = mock_conn.send_command.call_args_list
        assert calls[0][0] == (
            "gh_connect_components",
            {
                "source_instance_id": "src",
                "source_output_index": 0,
                "target_nickname": "Circle",
                "target_input_name": "Radius",
            },
        )
        assert calls[1][0] == (
            "gh_disconnect_components",
            {"disconnect_all": True, "target_instance_id": "dst"},
        )
        assert calls[2][0] == (
            "gh_set_parameter_value",
            {
                "value": 7.5,
                "input_index": 0,
                "nickname": "Radius",
                "input_name": "R",
                "min": 0,
                "max": 10,
                "decimals": 2,
            },
        )
        assert calls[3][0] == (
            "gh_get_parameter_value",
            {"output_index": 0, "max_items": 12, "instance_id": "circle-id", "output_name": "C"},
        )


class TestToolAnnotations:
    """Source-level guard that the readOnly/destructive ToolAnnotations stay attached.
    A live-runtime check is fragile under pytest's import ordering, but the source
    pattern is what actually drives the annotation, so checking it catches drift."""

    def _module_source(self, rel_path):
        from pathlib import Path
        root = Path(__file__).parent.parent / "src" / "rhinomcp"
        return (root / rel_path).read_text()

    def test_read_only_tools_marked(self):
        for rel in [
            "tools/get_document_summary.py",
            "tools/get_objects.py",
            "tools/get_object_info.py",
            "tools/object_attributes.py",
            "tools/analyze_objects.py",
            "tools/get_selected_objects_info.py",
            "tools/get_commands.py",
            "tools/rhinoscript_docs.py",
            "tools/grasshopper_catalog.py",
            "tools/grasshopper_components.py",
            "tools/grasshopper_document.py",
            "tools/grasshopper_graph.py",
            "tools/grasshopper_parameters.py",
        ]:
            src = self._module_source(rel)
            assert "readOnlyHint=True" in src, f"{rel} missing readOnlyHint annotation"

    def test_destructive_tools_marked(self):
        for rel in [
            "tools/delete_object.py",
            "tools/delete_layer.py",
            "tools/run_command.py",
            "tools/execute_rhinoscript_python_code.py",
            "tools/execute_rhinocommon_csharp_code.py",
            "tools/grasshopper_components.py",
            "tools/grasshopper_graph.py",
        ]:
            src = self._module_source(rel)
            assert "destructiveHint=True" in src, f"{rel} missing destructiveHint annotation"


class TestPackageApi:
    """Lock in that the rhinomcp package re-exports tool functions at the top level.

    Slice 3 replaced the manual import list in __init__.py with auto-discovery.
    We preserve the pre-existing package API (`from rhinomcp import <tool>`) by
    re-exporting tool-module callables during discovery; these tests guard that.
    """

    def test_classic_tools_are_top_level_attrs(self):
        import rhinomcp
        # A representative sample across tool categories — covers single-method
        # modules and modules that export multiple functions.
        for name in [
            "create_object",
            "delete_object",
            "create_layer",
            "boolean_union",
            "boolean_intersection",
            "loft",
            "pipe",
            "undo",
            "redo",
            "analyze_objects",
            "gh_create_document",
            "gh_get_document_info",
            "gh_search_components",
            "gh_get_graph",
            "gh_clear_graph",
            "gh_build_graph",
            "gh_mutate_graph",
            "gh_add_component",
            "gh_layout_components",
            "gh_run_solution",
            "gh_clear_canvas",
        ]:
            assert hasattr(rhinomcp, name), f"rhinomcp.{name} missing — re-export regression"
            assert callable(getattr(rhinomcp, name))

    def test_new_slice1_tools_are_top_level_attrs(self):
        import rhinomcp
        assert callable(getattr(rhinomcp, "run_command", None))
        assert callable(getattr(rhinomcp, "get_commands", None))

    def test_private_names_are_not_exported(self):
        import rhinomcp
        # The discovery loop skips names starting with "_"; verify nothing internal leaked.
        leaked = [n for n in dir(rhinomcp) if n in {"_TOOLS_DIR", "_info", "_mod", "_attr", "_value"}]
        assert not leaked, f"loop locals leaked into package namespace: {leaked}"
