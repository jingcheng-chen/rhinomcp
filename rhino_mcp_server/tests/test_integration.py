"""
Integration tests using the mock Rhino server.

These tests verify the full flow from MCP tools through to the server response.
"""

import pytest
import time
from tests.mock_rhino_server import MockRhinoServer


@pytest.fixture(scope="module")
def mock_server():
    """Start mock server for the test module."""
    server = MockRhinoServer(port=19999)  # Use different port to avoid conflicts
    server.start()
    time.sleep(0.1)  # Give server time to start

    # Patch the connection to use our test port
    import rhinomcp.server as srv
    original_port = srv.RHINO_PORT
    srv.RHINO_PORT = 19999

    # Reset global connection
    srv._rhino_connection = None

    yield server

    # Cleanup
    srv.RHINO_PORT = original_port
    srv._rhino_connection = None
    server.stop()


class TestCreateObject:
    """Integration tests for create_object."""

    def test_create_box(self, mock_server):
        """Test creating a box."""
        from rhinomcp.server import get_rhino_connection

        # Reset connection for fresh start
        import rhinomcp.server as srv
        srv._rhino_connection = None

        conn = get_rhino_connection()
        result = conn.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox",
            "params": {"width": 1, "length": 2, "height": 3}
        })

        assert result["name"] == "TestBox"
        assert result["type"] == "BOX"
        assert "id" in result

    def test_create_sphere_with_color(self, mock_server):
        """Test creating a sphere with color."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()
        result = conn.send_command("create_object", {
            "type": "SPHERE",
            "name": "RedSphere",
            "color": [255, 0, 0],
            "params": {"radius": 5}
        })

        assert result["name"] == "RedSphere"
        assert result["color"]["r"] == 255

    def test_create_multiple_objects(self, mock_server):
        """Test batch object creation."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()
        result = conn.send_command("create_objects", {
            "Box1": {"type": "BOX", "name": "Box1", "params": {"width": 1, "length": 1, "height": 1}},
            "Box2": {"type": "BOX", "name": "Box2", "params": {"width": 2, "length": 2, "height": 2}}
        })

        assert result["success_count"] == 2
        assert result["failure_count"] == 0


class TestModifyObject:
    """Integration tests for modify_object."""

    def test_rename_object(self, mock_server):
        """Test renaming an object."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create object first
        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "OriginalName",
            "params": {}
        })

        # Rename it
        result = conn.send_command("modify_object", {
            "id": created["id"],
            "new_name": "NewName"
        })

        assert result["name"] == "NewName"

    def test_change_color(self, mock_server):
        """Test changing object color."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "SPHERE",
            "name": "ColorTest",
            "params": {}
        })

        result = conn.send_command("modify_object", {
            "id": created["id"],
            "new_color": [0, 255, 0]
        })

        assert result["color"]["g"] == 255


class TestDeleteObject:
    """Integration tests for delete_object."""

    def test_delete_by_id(self, mock_server):
        """Test deleting object by ID."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "ToDelete",
            "params": {}
        })

        result = conn.send_command("delete_object", {"id": created["id"]})

        assert result["deleted"] is True

    def test_delete_all(self, mock_server):
        """Test deleting all objects."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create some objects
        conn.send_command("create_object", {"type": "BOX", "params": {}})
        conn.send_command("create_object", {"type": "SPHERE", "params": {}})

        result = conn.send_command("delete_object", {"all": True})

        assert result["deleted"] is True


class TestUndoRedo:
    """Integration tests for undo/redo."""

    def test_undo_single(self, mock_server):
        """Test undoing a single operation."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create an object (pushes to undo stack)
        conn.send_command("create_object", {"type": "BOX", "params": {}})

        result = conn.send_command("undo", {"steps": 1})

        assert result["undone_steps"] == 1

    def test_undo_multiple(self, mock_server):
        """Test undoing multiple operations."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create multiple objects
        conn.send_command("create_object", {"type": "BOX", "params": {}})
        conn.send_command("create_object", {"type": "SPHERE", "params": {}})
        conn.send_command("create_object", {"type": "CYLINDER", "params": {}})

        result = conn.send_command("undo", {"steps": 2})

        assert result["undone_steps"] == 2

    def test_redo(self, mock_server):
        """Test redo after undo."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_object", {"type": "BOX", "params": {}})
        conn.send_command("undo", {"steps": 1})

        result = conn.send_command("redo", {"steps": 1})

        assert result["redone_steps"] == 1


class TestBooleanOperations:
    """Integration tests for boolean operations."""

    def test_boolean_union(self, mock_server):
        """Test boolean union."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create two objects
        obj1 = conn.send_command("create_object", {"type": "BOX", "params": {}})
        obj2 = conn.send_command("create_object", {"type": "BOX", "params": {}})

        result = conn.send_command("boolean_union", {
            "object_ids": [obj1["id"], obj2["id"]],
            "name": "UnionResult"
        })

        assert result["count"] == 1
        assert len(result["result_ids"]) == 1

    def test_boolean_difference(self, mock_server):
        """Test boolean difference."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        base = conn.send_command("create_object", {"type": "BOX", "params": {}})
        subtract = conn.send_command("create_object", {"type": "SPHERE", "params": {}})

        result = conn.send_command("boolean_difference", {
            "base_id": base["id"],
            "subtract_ids": [subtract["id"]]
        })

        assert result["count"] == 1

    def test_boolean_intersection(self, mock_server):
        """Test boolean intersection."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        obj1 = conn.send_command("create_object", {"type": "BOX", "params": {}})
        obj2 = conn.send_command("create_object", {"type": "SPHERE", "params": {}})

        result = conn.send_command("boolean_intersection", {
            "object_ids": [obj1["id"], obj2["id"]]
        })

        assert result["count"] == 1


class TestLayers:
    """Integration tests for layer operations."""

    def test_create_layer(self, mock_server):
        """Test creating a layer."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        result = conn.send_command("create_layer", {
            "name": "TestLayer",
            "color": [100, 150, 200]
        })

        assert result["name"] == "TestLayer"
        assert result["color"]["r"] == 100

    def test_set_current_layer(self, mock_server):
        """Test setting current layer."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_layer", {"name": "NewLayer"})
        result = conn.send_command("get_or_set_current_layer", {"name": "NewLayer"})

        assert result["name"] == "NewLayer"

    def test_delete_layer(self, mock_server):
        """Test deleting a layer."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_layer", {"name": "ToDeleteLayer"})
        result = conn.send_command("delete_layer", {"name": "ToDeleteLayer"})

        assert result["deleted"] is True


class TestDocumentInfo:
    """Integration tests for document summary."""

    def test_get_document_summary(self, mock_server):
        """Test getting document summary."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create some objects
        conn.send_command("create_object", {"type": "BOX", "name": "DocInfoBox", "params": {}})

        result = conn.send_command("get_document_summary", {})

        assert "objects_by_type" in result
        assert "objects_by_layer" in result
        assert "layer_hierarchy" in result
        assert result["object_count"] >= 1
