"""
Integration tests using the mock Rhino server.

These tests verify the full flow from MCP tools through to the server response.
"""

import json
import pytest
import socket
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
            "params": {"width": 1, "length": 1, "height": 1}
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
            "params": {"radius": 1}
        })

        result = conn.send_command("modify_object", {
            "id": created["id"],
            "new_color": [0, 255, 0]
        })

        assert result["color"]["g"] == 255


class TestObjectAttributes:
    """Integration tests for object attribute read/update commands."""

    def test_get_and_update_object_attributes(self, mock_server):
        """Test reading and updating user strings and common metadata."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_layer", {"name": "Parts"})
        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "RawBox",
            "params": {"width": 1, "length": 1, "height": 1}
        })

        updated = conn.send_command("update_object_attributes", {
            "id": created["id"],
            "new_name": "Panel",
            "layer": "Parts",
            "color": [10, 20, 30],
            "user_strings": {"PartNo": "A-100", "Count": 3}
        })

        assert updated["name"] == "Panel"
        assert updated["layer"]["name"] == "Parts"
        assert updated["color"]["r"] == 10
        assert updated["user_strings"]["PartNo"] == "A-100"
        assert updated["user_strings"]["Count"] == "3"

        attributes = conn.send_command("get_object_attributes", {"id": created["id"]})

        assert attributes["name"] == "Panel"
        assert attributes["user_strings"]["PartNo"] == "A-100"

    def test_update_object_attributes_deletes_user_strings(self, mock_server):
        """Test deleting user strings without shipping full object geometry."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "AttrBox",
            "params": {"width": 1, "length": 1, "height": 1}
        })
        conn.send_command("update_object_attributes", {
            "id": created["id"],
            "user_strings": {"Keep": "yes", "Drop": "no"}
        })

        updated = conn.send_command("update_object_attributes", {
            "id": created["id"],
            "delete_user_strings": ["Drop"]
        })

        assert updated["user_strings"] == {"Keep": "yes"}

    def test_update_object_attributes_clears_material_index(self, mock_server):
        """material_index=-1 restores layer material inheritance."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "MaterialBox",
            "params": {"width": 1, "length": 1, "height": 1}
        })
        conn.send_command("update_object_attributes", {
            "id": created["id"],
            "material_index": 0
        })

        updated = conn.send_command("update_object_attributes", {
            "id": created["id"],
            "material_index": -1
        })

        assert updated["material_index"] == -1
        assert updated["material_source"] == "MaterialFromLayer"


class TestAnalyzeObjects:
    """Integration tests for analyze_objects."""

    def test_analyze_line_length(self, mock_server):
        """Analyze a line and get length/bounding-box feedback."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "LINE",
            "name": "MeasuredLine",
            "params": {"start": [0, 0, 0], "end": [3, 4, 0]}
        })

        result = conn.send_command("analyze_objects", {"id": created["id"]})

        assert result["object_count"] == 1
        analysis = result["analyses"][0]
        assert analysis["valid"] is True
        assert analysis["type"] == "LINE"
        assert analysis["metrics"]["length"] == 5

    def test_analyze_multiple_objects(self, mock_server):
        """Analyze multiple objects in one command."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        box = conn.send_command("create_object", {
            "type": "BOX",
            "name": "MeasuredBox",
            "params": {"width": 2, "length": 3, "height": 4}
        })
        line = conn.send_command("create_object", {
            "type": "LINE",
            "name": "MeasuredLine2",
            "params": {"start": [0, 0, 0], "end": [1, 0, 0]}
        })

        result = conn.send_command("analyze_objects", {"object_ids": [box["id"], line["id"]]})

        assert result["object_count"] == 2
        metrics_by_name = {item["name"]: item["metrics"] for item in result["analyses"]}
        assert metrics_by_name["MeasuredBox"]["volume"] == 24
        assert metrics_by_name["MeasuredLine2"]["length"] == 1

    def test_analyze_rejects_empty_object_ids(self, mock_server):
        """Empty object_ids is invalid even when validation only warns."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        with pytest.raises(Exception, match="at least one id"):
            conn.send_command("analyze_objects", {"object_ids": []})


class TestDeleteObject:
    """Integration tests for delete_object."""

    def test_delete_by_id(self, mock_server):
        """Test deleting object by ID."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        created = conn.send_command("create_object", {
            "type": "BOX",
            "name": "ToDelete",
            "params": {"width": 1, "length": 1, "height": 1}
        })

        result = conn.send_command("delete_object", {"id": created["id"]})

        assert result["deleted"] is True

    def test_delete_all(self, mock_server):
        """Test deleting all objects. The mock must return the same shape as
        C# (deleted, count, scope:'all') — the wrapper relied on `name` and
        would crash on a successful delete-all before P0.2."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create some objects
        conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        conn.send_command("create_object", {"type": "SPHERE", "params": {"radius": 1}})

        result = conn.send_command("delete_object", {"all": True})

        assert result["deleted"] is True
        assert result["scope"] == "all"
        assert "count" in result
        # The successful response must NOT include a "name" — confirming the
        # wrapper has to branch on scope/count rather than assuming `name`.
        assert "name" not in result


class TestUndoRedo:
    """Integration tests for undo/redo."""

    def test_undo_single(self, mock_server):
        """Test undoing a single operation."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create an object (pushes to undo stack)
        conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})

        result = conn.send_command("undo", {"steps": 1})

        assert result["undone_steps"] == 1

    def test_undo_multiple(self, mock_server):
        """Test undoing multiple operations."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        # Create multiple objects
        conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        conn.send_command("create_object", {"type": "SPHERE", "params": {"radius": 1}})
        conn.send_command("create_object", {"type": "CYLINDER", "params": {"radius": 1, "height": 2}})

        result = conn.send_command("undo", {"steps": 2})

        assert result["undone_steps"] == 2

    def test_redo(self, mock_server):
        """Test redo after undo."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
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
        obj1 = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        obj2 = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})

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

        base = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        subtract = conn.send_command("create_object", {"type": "SPHERE", "params": {"radius": 1}})

        result = conn.send_command("boolean_difference", {
            "base_id": base["id"],
            "subtract_ids": [subtract["id"]]
        })

        assert result["count"] == 1

    def test_boolean_intersection(self, mock_server):
        """Test boolean intersection."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        obj1 = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        obj2 = conn.send_command("create_object", {"type": "SPHERE", "params": {"radius": 1}})

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
        conn.send_command("create_object", {"type": "BOX", "name": "DocInfoBox", "params": {"width": 1, "length": 1, "height": 1}})

        result = conn.send_command("get_document_summary", {})

        assert "objects_by_type" in result
        assert "objects_by_layer" in result
        assert "layer_hierarchy" in result
        assert result["object_count"] >= 1


class TestAdvancedGeometry:
    """Smoke tests for the geometry commands added with the schema fill-in.

    These exercise the wire path end-to-end against the mock so a shape
    mismatch between schema / Python wrapper / mock surface is caught by
    CI instead of silently passing unit tests that mock send_command.
    """

    def test_loft(self, mock_server):
        from rhinomcp.server import get_rhino_connection
        conn = get_rhino_connection()
        c1 = conn.send_command("create_object", {"type": "LINE", "params": {"start": [0, 0, 0], "end": [1, 0, 0]}})
        c2 = conn.send_command("create_object", {"type": "LINE", "params": {"start": [0, 1, 0], "end": [1, 1, 0]}})
        result = conn.send_command("loft", {"curve_ids": [c1["id"], c2["id"]]})
        assert result["count"] == 1
        assert result["result_ids"]

    def test_extrude_curve(self, mock_server):
        from rhinomcp.server import get_rhino_connection
        conn = get_rhino_connection()
        c = conn.send_command("create_object", {"type": "LINE", "params": {"start": [0, 0, 0], "end": [1, 0, 0]}})
        result = conn.send_command("extrude_curve", {"curve_id": c["id"], "direction": [0, 0, 1]})
        assert result["result_id"]

    def test_pipe_rejects_zero_radius(self, mock_server):
        from rhinomcp.server import get_rhino_connection
        conn = get_rhino_connection()
        c = conn.send_command("create_object", {"type": "LINE", "params": {"start": [0, 0, 0], "end": [1, 0, 0]}})
        with pytest.raises(Exception, match="radius"):
            conn.send_command("pipe", {"curve_id": c["id"], "radius": 0})

    def test_modify_objects(self, mock_server):
        from rhinomcp.server import get_rhino_connection
        conn = get_rhino_connection()
        a = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        b = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        result = conn.send_command("modify_objects", {
            "objects": [
                {"id": a["id"], "new_name": "A2"},
                {"id": b["id"], "new_color": [255, 0, 0]},
            ]
        })
        assert result["success_count"] == 2
        assert result["failure_count"] == 0

    def test_capture_viewport_returns_decodable_image(self, mock_server):
        import base64
        from rhinomcp.server import get_rhino_connection
        conn = get_rhino_connection()
        result = conn.send_command("capture_viewport", {"viewport": "perspective", "width": 100, "height": 100})
        # image_data must be valid base64 the wrapper can decode.
        base64.b64decode(result["image_data"])
        assert result["viewport_name"] == "perspective"


class TestPerceptionPassthrough:
    """End-to-end: the create/modify tool wrappers must surface the spatial
    feedback (bounding_box) the plugin serializes, through the full
    wrapper -> socket -> plugin -> wrapper path. This is the CI-runnable
    end-to-end of Scene Perception Layer stage 0, against the mock whose
    create/modify responses mirror the plugin's Serializer.RhinoObject shape.

    The wrappers' get_rhino_connection is monkeypatched to a connection aimed
    explicitly at the mock port. That keeps the test hermetic: it can never
    fall back to a real Rhino on the default port (which would mutate a live
    document), and it doesn't depend on module-reload ordering elsewhere in the
    suite that can leave the wrapper's import-time binding pointed at the
    default port.
    """

    def _mock_conn(self, monkeypatch):
        from rhinomcp.server import RhinoConnection
        import rhinomcp.tools.create_object as create_mod
        import rhinomcp.tools.modify_object as modify_mod

        conn = RhinoConnection(host="127.0.0.1", port=19999)
        monkeypatch.setattr(create_mod, "get_rhino_connection", lambda: conn)
        monkeypatch.setattr(modify_mod, "get_rhino_connection", lambda: conn)
        return create_mod.create_object, modify_mod.modify_object

    def test_create_wrapper_surfaces_bounding_box(self, mock_server, monkeypatch):
        create_object, _ = self._mock_conn(monkeypatch)

        result = create_object(
            ctx=None, type="BOX", name="PerceptionBox",
            params={"width": 1, "length": 1, "height": 1},
        )

        assert result["success"] is True
        assert result["id"] is not None
        # The bbox the plugin computed is now visible to the client end to end.
        assert result["bounding_box"] == [[-1, -1, -1], [1, 1, 1]]

    def test_modify_wrapper_surfaces_bounding_box(self, mock_server, monkeypatch):
        create_object, modify_object = self._mock_conn(monkeypatch)

        created = create_object(
            ctx=None, type="BOX", name="ToMove",
            params={"width": 1, "length": 1, "height": 1},
        )
        moved = modify_object(ctx=None, id=created["id"], translation=[5, 0, 0])

        assert moved["success"] is True
        # A modify now reports the object's extent rather than just id/name.
        assert "bounding_box" in moved
class TestWireProtocol:
    """Wire-level tests against the mock server, which mirrors the plugin's
    framing logic: framed protocol for new clients, legacy bare JSON for old
    ones, decided by the first byte of the connection."""

    def _read_frame(self, sock):
        header = b""
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            assert chunk, "connection closed mid-header"
            header += chunk
        length = int.from_bytes(header, "big")
        body = b""
        while len(body) < length:
            chunk = sock.recv(length - len(body))
            assert chunk, "connection closed mid-body"
            body += chunk
        return json.loads(body.decode("utf-8"))

    def test_pipelined_framed_commands_all_answered_in_order(self, mock_server):
        """The regression that motivated framing: two commands in one TCP
        write. The old whole-buffer JObject.Parse approach could never parse
        the concatenation, wedging the connection with both commands lost.
        With framing both execute and answer in order."""
        cmd1 = json.dumps({"type": "get_document_summary", "params": {}}).encode("utf-8")
        cmd2 = json.dumps({"type": "get_objects", "params": {}}).encode("utf-8")
        wire = (
            len(cmd1).to_bytes(4, "big") + cmd1
            + len(cmd2).to_bytes(4, "big") + cmd2
        )

        sock = socket.create_connection(("127.0.0.1", 19999), timeout=5)
        try:
            sock.sendall(wire)
            first = self._read_frame(sock)
            second = self._read_frame(sock)
        finally:
            sock.close()

        assert first["status"] == "success"
        assert "object_count" in first["result"]  # document summary
        assert second["status"] == "success"
        assert "objects" in second["result"]  # get_objects result

    def test_legacy_unframed_client_still_works(self, mock_server):
        """A pre-framing client sends bare JSON and expects bare JSON back.
        The first-byte sniff must route it onto the legacy path."""
        cmd = json.dumps({"type": "get_document_summary", "params": {}}).encode("utf-8")

        sock = socket.create_connection(("127.0.0.1", 19999), timeout=5)
        try:
            sock.sendall(cmd)
            sock.settimeout(5)
            data = b""
            while True:
                data += sock.recv(65536)
                try:
                    response = json.loads(data.decode("utf-8"))
                    break
                except json.JSONDecodeError:
                    continue
        finally:
            sock.close()

        # Bare JSON back: the first byte is '{', not a length header.
        assert data[0:1] == b"{"
        assert response["status"] == "success"

    def test_malformed_frame_gets_error_and_connection_survives(self, mock_server):
        """A well-framed message carrying bad JSON must not take the whole
        connection down with it. Framing pins where the next frame starts, so
        the bad one gets an error response and the command queued behind it is
        still answered. This pins the contract the plugin has to meet."""
        good1 = json.dumps({"type": "get_document_summary", "params": {}}).encode("utf-8")
        bad = b"{not valid json"
        good2 = json.dumps({"type": "get_objects", "params": {}}).encode("utf-8")
        wire = (
            len(good1).to_bytes(4, "big") + good1
            + len(bad).to_bytes(4, "big") + bad
            + len(good2).to_bytes(4, "big") + good2
        )

        sock = socket.create_connection(("127.0.0.1", 19999), timeout=5)
        try:
            sock.sendall(wire)
            first = self._read_frame(sock)
            second = self._read_frame(sock)
            third = self._read_frame(sock)
        finally:
            sock.close()

        # The good commands before and after the bad frame both succeed, in
        # order; the bad one comes back as an error rather than a dropped
        # connection (which would hang _read_frame on the third reply).
        assert first["status"] == "success"
        assert "object_count" in first["result"]
        assert second["status"] == "error"
        assert third["status"] == "success"
        assert "objects" in third["result"]
