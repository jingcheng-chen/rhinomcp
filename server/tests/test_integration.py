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


@pytest.fixture
def legacy_mock_server():
    """A plugin from before dry_run existed, on its own port. Tests reach it
    through an explicit connection, so the global one is left alone."""
    server = MockRhinoServer(port=19998, legacy_plugin=True)
    server.start()
    time.sleep(0.1)

    yield server

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

    def test_boolean_union_dry_run_predicts_then_commits(self, mock_server):
        """A dry_run union returns a prediction and leaves the document
        untouched; the same inputs then commit for real."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        obj1 = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        obj2 = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})

        before = conn.send_command("get_document_summary", {})["object_count"]

        prediction = conn.send_command("boolean_union", {
            "object_ids": [obj1["id"], obj2["id"]],
            "dry_run": True,
        })

        after = conn.send_command("get_document_summary", {})["object_count"]

        assert prediction["dry_run"] is True
        assert prediction["would_succeed"] is True
        assert prediction["count"] == 1
        assert "result_ids" not in prediction
        entry = prediction["results"][0]
        assert entry["valid"] is True
        assert entry["is_solid"] is True
        assert entry["volume"] > 0
        assert "area" in entry
        assert "bounding_box" in entry

        # The preview added and removed nothing, so both inputs still resolve.
        assert after == before
        conn.send_command("get_object_info", {"id": obj1["id"]})
        conn.send_command("get_object_info", {"id": obj2["id"]})

        committed = conn.send_command("boolean_union", {
            "object_ids": [obj1["id"], obj2["id"]],
            "name": "CommittedUnion",
        })
        assert committed["count"] == 1
        assert len(committed["result_ids"]) == 1

    def test_boolean_difference_dry_run_leaves_inputs(self, mock_server):
        """A dry_run difference previews without deleting the base or subtract
        inputs."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        base = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
        subtract = conn.send_command("create_object", {"type": "SPHERE", "params": {"radius": 1}})

        prediction = conn.send_command("boolean_difference", {
            "base_id": base["id"],
            "subtract_ids": [subtract["id"]],
            "dry_run": True,
        })

        assert prediction["dry_run"] is True
        assert "result_ids" not in prediction
        assert prediction["results"][0]["bounding_box"] is not None
        conn.send_command("get_object_info", {"id": base["id"]})
        conn.send_command("get_object_info", {"id": subtract["id"]})


class TestDryRunContract:
    """dry_run is a declared, per-command capability: unsupported commands
    reject it, and both boolean shapes hold up under strict response validation."""

    def test_dry_run_rejected_on_unsupported_command(self, mock_server):
        """create_object does not declare dry_run support, so the client refuses
        to send it at all: the flag never reaches the plugin."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_VALIDATE
        srv._rhino_connection = None
        srv.RHINO_VALIDATE = "off"  # bypass pre-flight so only the gate can refuse
        mock_server.received_commands.clear()
        try:
            conn = get_rhino_connection()
            with pytest.raises(Exception, match="does not report dry_run support"):
                conn.send_command("create_object", {
                    "type": "BOX",
                    "params": {"width": 1, "length": 1, "height": 1},
                    "dry_run": True,
                })
        finally:
            srv.RHINO_VALIDATE = original
            srv._rhino_connection = None

        assert "create_object" not in mock_server.received_commands

    def test_plugin_still_rejects_dry_run_it_cannot_honor(self, mock_server):
        """The plugin keeps its own fail-closed check for clients that don't gate,
        mirroring the dispatcher in RhinoMCPServer.ExecuteCommandInternal."""
        response = mock_server._process_command({
            "type": "create_object",
            "params": {
                "type": "BOX",
                "params": {"width": 1, "length": 1, "height": 1},
                "dry_run": True,
            },
        })

        assert response["status"] == "error"
        assert "does not support dry_run" in response["message"]

    def test_real_and_dry_run_validate_in_strict_mode(self, mock_server):
        """Under strict response validation, a real boolean and a dry_run boolean
        both pass responses/boolean_result.json; a shape drift would raise here."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_VALIDATE
        srv._rhino_connection = None
        srv.RHINO_VALIDATE = "strict"
        try:
            conn = get_rhino_connection()
            a = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})
            b = conn.send_command("create_object", {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}})

            preview = conn.send_command("boolean_union", {
                "object_ids": [a["id"], b["id"]],
                "dry_run": True,
            })
            assert preview["dry_run"] is True
            assert "result_ids" not in preview

            committed = conn.send_command("boolean_union", {
                "object_ids": [a["id"], b["id"]],
                "name": "StrictUnion",
            })
            assert "result_ids" in committed
            assert committed["count"] == 1
        finally:
            srv.RHINO_VALIDATE = original
            srv._rhino_connection = None


class TestDryRunCapabilityGate:
    """The server and the plugin ship separately, so a server that knows dry_run
    can end up talking to a plugin that doesn't. That plugin drops the flag it
    has never heard of and runs the real boolean, deleting the sources, while the
    caller believes it asked for a preview. So the client refuses to send a
    preview unless the plugin advertises support for that exact command.

    Each test drives its own connection at an explicit port, the way
    TestPerceptionPassthrough does: hermetic, never able to fall back to a real
    Rhino on the default port, and immune to the module-reload ordering that can
    leave a wrapper's import-time binding pointed elsewhere.
    """

    def _connection(self, monkeypatch, port):
        from rhinomcp.server import RhinoConnection
        import rhinomcp.tools.boolean_operations as boolean_mod

        conn = RhinoConnection(host="127.0.0.1", port=port)
        monkeypatch.setattr(boolean_mod, "get_rhino_connection", lambda: conn)
        return conn

    def _two_boxes(self, conn):
        a = conn.send_command("create_object", {
            "type": "BOX", "name": "GateA",
            "params": {"width": 1, "length": 1, "height": 1}})
        b = conn.send_command("create_object", {
            "type": "BOX", "name": "GateB",
            "params": {"width": 1, "length": 1, "height": 1}})
        return a["id"], b["id"]

    def test_old_plugin_would_run_the_real_boolean(self, legacy_mock_server):
        """What the gate is there to stop, pinned: drive the old plugin directly
        and the dry_run union deletes both sources and reports real result ids."""
        a = legacy_mock_server._create_object({"type": "BOX", "name": "IgnoredA"})
        b = legacy_mock_server._create_object({"type": "BOX", "name": "IgnoredB"})

        response = legacy_mock_server._process_command({
            "type": "boolean_union",
            "params": {"object_ids": [a["id"], b["id"]], "dry_run": True},
        })

        assert response["status"] == "success"
        assert "result_ids" in response["result"]
        assert a["id"] not in legacy_mock_server.objects
        assert b["id"] not in legacy_mock_server.objects

    def test_union_dry_run_refused_and_sources_survive(self, legacy_mock_server, monkeypatch):
        conn = self._connection(monkeypatch, 19998)
        a, b = self._two_boxes(conn)
        before = set(legacy_mock_server.objects)

        with pytest.raises(Exception, match="does not report dry_run support"):
            conn.send_command("boolean_union", {
                "object_ids": [a, b],
                "delete_sources": True,
                "dry_run": True,
            })

        assert set(legacy_mock_server.objects) == before
        assert a in legacy_mock_server.objects
        assert b in legacy_mock_server.objects
        assert "boolean_union" not in legacy_mock_server.received_commands

    def test_difference_dry_run_refused_and_sources_survive(self, legacy_mock_server, monkeypatch):
        conn = self._connection(monkeypatch, 19998)
        base, subtract = self._two_boxes(conn)
        before = set(legacy_mock_server.objects)

        with pytest.raises(Exception, match="does not report dry_run support"):
            conn.send_command("boolean_difference", {
                "base_id": base,
                "subtract_ids": [subtract],
                "delete_sources": True,
                "dry_run": True,
            })

        assert set(legacy_mock_server.objects) == before
        assert base in legacy_mock_server.objects
        assert subtract in legacy_mock_server.objects
        assert "boolean_difference" not in legacy_mock_server.received_commands

    def test_intersection_dry_run_refused_and_sources_survive(self, legacy_mock_server, monkeypatch):
        conn = self._connection(monkeypatch, 19998)
        a, b = self._two_boxes(conn)
        before = set(legacy_mock_server.objects)

        with pytest.raises(Exception, match="does not report dry_run support"):
            conn.send_command("boolean_intersection", {
                "object_ids": [a, b],
                "delete_sources": True,
                "dry_run": True,
            })

        assert set(legacy_mock_server.objects) == before
        assert a in legacy_mock_server.objects
        assert b in legacy_mock_server.objects
        assert "boolean_intersection" not in legacy_mock_server.received_commands

    def test_the_wrapper_surfaces_the_refusal_as_a_tool_error(self, legacy_mock_server, monkeypatch):
        """What the user gets: asking boolean_union for a preview against an old
        plugin fails the tool call and leaves both objects standing."""
        from rhinomcp.tools.boolean_operations import boolean_union

        conn = self._connection(monkeypatch, 19998)
        a, b = self._two_boxes(conn)
        before = set(legacy_mock_server.objects)

        with pytest.raises(Exception, match="does not report dry_run support"):
            boolean_union(ctx=None, object_ids=[a, b], dry_run=True)

        assert set(legacy_mock_server.objects) == before

    def test_old_plugin_serves_a_normal_boolean_unchanged(self, legacy_mock_server, monkeypatch):
        """Without dry_run nothing else is gated: after the one capabilities read
        every connection makes, the command goes straight out and the old plugin
        is served exactly as it was before."""
        from rhinomcp.tools.boolean_operations import boolean_union

        conn = self._connection(monkeypatch, 19998)
        a, b = self._two_boxes(conn)

        result = boolean_union(ctx=None, object_ids=[a, b], name="OldPluginUnion")

        assert "Boolean union created" in result
        assert legacy_mock_server.received_commands.count("describe_capabilities") == 1

    def test_dry_run_runs_end_to_end_when_the_plugin_advertises_it(self, mock_server, monkeypatch):
        from rhinomcp.tools.boolean_operations import boolean_union

        conn = self._connection(monkeypatch, 19999)
        a, b = self._two_boxes(conn)

        result = boolean_union(ctx=None, object_ids=[a, b], dry_run=True)

        assert "Boolean union would create" in result
        assert "Predicted results" in result
        assert a in mock_server.objects
        assert b in mock_server.objects

    def test_capabilities_read_once_per_connection(self, mock_server, monkeypatch):
        """The answer is cached, so several previews share one lookup, and the
        lookup itself never re-enters the gate."""
        from rhinomcp.tools.boolean_operations import boolean_union

        conn = self._connection(monkeypatch, 19999)
        mock_server.received_commands.clear()
        a, b = self._two_boxes(conn)

        for _ in range(3):
            boolean_union(ctx=None, object_ids=[a, b], dry_run=True)

        assert mock_server.received_commands.count("describe_capabilities") == 1
        assert mock_server.received_commands.count("boolean_union") == 3

    def test_reconnect_rereads_capabilities(self, mock_server, monkeypatch):
        """A reconnect can land on a different plugin, so the cached answer dies
        with the socket."""
        from rhinomcp.tools.boolean_operations import boolean_union

        conn = self._connection(monkeypatch, 19999)
        mock_server.received_commands.clear()
        a, b = self._two_boxes(conn)

        boolean_union(ctx=None, object_ids=[a, b], dry_run=True)
        conn.disconnect()
        boolean_union(ctx=None, object_ids=[a, b], dry_run=True)

        assert mock_server.received_commands.count("describe_capabilities") == 2

    def test_describe_capabilities_is_callable_normally(self, mock_server, monkeypatch):
        """The gate reads capabilities by sending describe_capabilities, so that
        command has to stay callable in its own right."""
        conn = self._connection(monkeypatch, 19999)

        result = conn.send_command("describe_capabilities", {})

        by_name = {c["name"]: c for c in result["commands"]}
        assert by_name["boolean_union"]["supports_dry_run"] is True
        assert by_name["create_object"]["supports_dry_run"] is False


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

    def test_deleting_a_deleted_layer_is_not_found(self, mock_server):
        """A layer already deleted counts as missing, as in get_or_set_current_layer."""
        from rhinomcp.server import get_rhino_connection

        conn = get_rhino_connection()

        conn.send_command("create_layer", {"name": "DeletedTwice"})
        conn.send_command("delete_layer", {"name": "DeletedTwice"})
        with pytest.raises(Exception, match=r"^not_found: Layer 'DeletedTwice' not found"):
            conn.send_command("delete_layer", {"name": "DeletedTwice"})


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
        assert result["viewport_name"] == "Perspective"


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


class TestChangeDeltaPerception:
    """End-to-end: with perception enabled the server forwards include_delta and
    mutating commands come back with a _delta block reporting created/deleted
    ids and counts; with it disabled nothing changes. Runs against the mock,
    whose dispatch mirrors the plugin's delta attachment."""

    def _enable(self):
        import rhinomcp.server as srv
        srv._rhino_connection = None
        srv.RHINO_PERCEPTION = True

    def _restore(self, value):
        import rhinomcp.server as srv
        srv.RHINO_PERCEPTION = value
        srv._rhino_connection = None

    def test_create_carries_delta_when_enabled(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            result = conn.send_command("create_object", {
                "type": "BOX", "name": "DeltaBox",
                "params": {"width": 1, "length": 1, "height": 1},
            })
        finally:
            self._restore(original)

        assert "_delta" in result
        d = result["_delta"]
        assert d["created_count"] == 1
        assert d["deleted_count"] == 0
        assert d["truncated"] is False
        # The id list is included because the count is within the cap.
        assert result["id"] in d["created_ids"]
        assert d["deleted_ids"] == []
        assert d["count_after"] == d["count_before"] + 1

    def test_delete_carries_delta_when_enabled(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            created = conn.send_command("create_object", {
                "type": "BOX", "name": "ToDelete",
                "params": {"width": 1, "length": 1, "height": 1},
            })
            deleted = conn.send_command("delete_object", {"id": created["id"]})
        finally:
            self._restore(original)

        dd = deleted["_delta"]
        assert dd["deleted_count"] == 1
        assert dd["created_count"] == 0
        assert dd["truncated"] is False
        assert created["id"] in dd["deleted_ids"]
        assert dd["created_ids"] == []
        assert dd["count_after"] == dd["count_before"] - 1

    def test_no_delta_when_disabled(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        import rhinomcp.server as _srv
        _srv._rhino_connection = None
        _srv.RHINO_PERCEPTION = False
        try:
            conn = get_rhino_connection()
            result = conn.send_command("create_object", {
                "type": "BOX", "name": "NoDeltaBox",
                "params": {"width": 1, "length": 1, "height": 1},
            })
        finally:
            self._restore(original)

        assert "_delta" not in result

    def test_dry_run_carries_no_delta_or_health(self, mock_server):
        """A dry_run mutates nothing, so with perception on it still comes back
        with no _delta or _health block."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            obj1 = conn.send_command("create_object", {
                "type": "BOX", "name": "DryDeltaA",
                "params": {"width": 1, "length": 1, "height": 1},
            })
            obj2 = conn.send_command("create_object", {
                "type": "BOX", "name": "DryDeltaB",
                "params": {"width": 1, "length": 1, "height": 1},
            })
            prediction = conn.send_command("boolean_union", {
                "object_ids": [obj1["id"], obj2["id"]],
                "dry_run": True,
            })
        finally:
            self._restore(original)

        assert prediction["dry_run"] is True
        assert "_delta" not in prediction
        assert "_health" not in prediction

    def test_large_op_truncates_id_lists(self, mock_server):
        """A single operation that creates more than the cap reports exact
        counts but omits the id arrays and sets truncated=true, so a
        thousand-object operation can't flood the client's context."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            specs = {
                f"B{i}": {
                    "type": "BOX", "name": f"BulkBox{i}",
                    "params": {"width": 1, "length": 1, "height": 1},
                }
                for i in range(60)
            }
            result = conn.send_command("create_objects", specs)
        finally:
            self._restore(original)

        d = result["_delta"]
        assert d["created_count"] == 60          # exact count is always there
        assert d["truncated"] is True
        assert "created_ids" not in d            # omitted because over the cap
        assert d["deleted_count"] == 0
        assert d["deleted_ids"] == []            # under the cap, so present


class TestChangeHealthPerception:
    """End-to-end: with perception enabled the server forwards include_health and
    mutating commands come back with a _health block reporting how many created
    objects were checked and which were invalid. The mock holds no real geometry,
    so it reports the all-clear shape; the invalid path is covered by the C# unit
    test, the live test, and the schema test."""

    def _enable(self):
        import rhinomcp.server as srv
        srv._rhino_connection = None
        srv.RHINO_PERCEPTION = True

    def _restore(self, value):
        import rhinomcp.server as srv
        srv.RHINO_PERCEPTION = value
        srv._rhino_connection = None

    def test_create_carries_health_when_enabled(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            result = conn.send_command("create_object", {
                "type": "BOX", "name": "HealthBox",
                "params": {"width": 1, "length": 1, "height": 1},
            })
        finally:
            self._restore(original)

        assert "_health" in result
        h = result["_health"]
        assert h["checked_count"] == 1
        assert h["invalid_count"] == 0
        assert h["issues"] == []
        assert h["truncated"] is False

    def test_perception_carries_both_delta_and_health(self, mock_server):
        """RHINO_PERCEPTION is one master switch, so a mutating command comes
        back with both perception blocks."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            result = conn.send_command("create_object", {
                "type": "BOX", "name": "BothBox",
                "params": {"width": 1, "length": 1, "height": 1},
            })
        finally:
            self._restore(original)

        assert "_delta" in result and "_health" in result
        assert result["_delta"]["created_count"] == 1
        assert result["_health"]["checked_count"] == 1

    def test_no_health_when_disabled(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        srv._rhino_connection = None
        srv.RHINO_PERCEPTION = False
        try:
            conn = get_rhino_connection()
            result = conn.send_command("create_object", {
                "type": "BOX", "name": "NoHealthBox",
                "params": {"width": 1, "length": 1, "height": 1},
            })
        finally:
            self._restore(original)

        assert "_health" not in result

    def test_readonly_has_no_health(self, mock_server):
        """Read-only commands never carry a _health, even with perception on."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        self._enable()
        try:
            conn = get_rhino_connection()
            result = conn.send_command("get_document_summary", {})
        finally:
            self._restore(original)

        assert "_health" not in result
        
class TestMeasureObjects:
    """End-to-end measure_objects through the mock: verifies the command wiring
    and the result shape. The exact spatial values come from real RhinoCommon
    geometry, which the mock can't model, so those are covered by the live test;
    here we pin that the contract shape arrives intact."""

    def test_measure_two_objects(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection
        srv._rhino_connection = None

        conn = get_rhino_connection()
        a = conn.send_command("create_object", {
            "type": "BOX", "name": "MeasA",
            "params": {"width": 1, "length": 1, "height": 1}})
        b = conn.send_command("create_object", {
            "type": "BOX", "name": "MeasB",
            "params": {"width": 1, "length": 1, "height": 1}})

        result = conn.send_command("measure_objects", {"object_ids": [a["id"], b["id"]]})

        assert result["object_a"] == a["id"]
        assert result["object_b"] == b["id"]
        assert isinstance(result["clash"], bool)
        assert result["bbox_gap"] >= 0
        assert result["method"] in ("brep", "curve", "bbox")
        assert result["intersection_count"] >= 0


class TestDescribeCapabilities:
    """End-to-end describe_capabilities through the mock: the server's
    self-description arrives with the command surface, read-only flags, and
    perception envelope flags intact."""

    def test_describe_capabilities_shape(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection
        srv._rhino_connection = None

        conn = get_rhino_connection()
        result = conn.send_command("describe_capabilities", {})

        assert isinstance(result["version"], str)
        assert result["command_count"] == len(result["commands"])
        for c in result["commands"]:
            assert isinstance(c["name"], str)
            assert isinstance(c["read_only"], bool)
        flags = [f["flag"] for f in result["perception"]["envelope_flags"]]
        assert "include_delta" in flags
        assert "include_health" in flags

    def test_describe_capabilities_is_readonly_no_delta(self, mock_server):
        """A read-only command carries no _delta even with perception on."""
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection

        original = srv.RHINO_PERCEPTION
        srv._rhino_connection = None
        srv.RHINO_PERCEPTION = True
        try:
            conn = get_rhino_connection()
            result = conn.send_command("describe_capabilities", {})
        finally:
            srv.RHINO_PERCEPTION = original
            srv._rhino_connection = None

        assert "_delta" not in result


class TestSectionProfile:
    """End-to-end section_profile through the mock: verifies command wiring and
    the result shape. The mock has no real geometry to slice, so exact areas come
    from the live Rhino test; here we pin that the contract shape arrives intact
    for both the single-plane and profile modes."""

    def test_section_plane_shape(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection
        srv._rhino_connection = None

        conn = get_rhino_connection()
        box = conn.send_command("create_object", {
            "type": "BOX", "name": "SecBox",
            "params": {"width": 2, "length": 2, "height": 2}})

        result = conn.send_command("section_profile", {
            "object_ids": [box["id"]],
            "plane": {"axis": "Z", "value": 0}})

        assert result["mode"] == "plane"
        assert result["object_count"] == 1
        assert "origin" in result["plane"] and "normal" in result["plane"]
        assert isinstance(result["total_section_area"], (int, float))
        assert len(result["profiles"]) == 1
        prof = result["profiles"][0]
        assert prof["id"] == box["id"]
        assert "loops" in prof and "section_area" in prof and "loop_count" in prof

    def test_section_profile_mode_shape(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection
        srv._rhino_connection = None

        conn = get_rhino_connection()
        box = conn.send_command("create_object", {
            "type": "BOX", "name": "SecProfBox",
            "params": {"width": 2, "length": 2, "height": 4}})

        result = conn.send_command("section_profile", {
            "id": box["id"],
            "profile": {"axis": "Z", "count": 5}})

        assert result["mode"] == "profile"
        assert result["axis"] == "Z"
        assert result["count"] == 5
        assert len(result["sections"]) == 5
        for s in result["sections"]:
            assert "position" in s and "total_section_area" in s and "loop_count" in s

    def test_section_requires_one_cut(self, mock_server):
        import rhinomcp.server as srv
        from rhinomcp.server import get_rhino_connection
        srv._rhino_connection = None

        conn = get_rhino_connection()
        box = conn.send_command("create_object", {
            "type": "BOX", "name": "SecBadBox",
            "params": {"width": 1, "length": 1, "height": 1}})

        with pytest.raises(Exception, match="exactly one of plane or profile"):
            conn.send_command("section_profile", {"id": box["id"]})


class TestCodedErrors:
    """A coded plugin error reaches the client as `code: message`, then the
    guidance on its own line; an uncoded error keeps its bare message.

    The mock answers the failures the plugin codes (unknown object id, unknown
    layer) with a code and guidance, exactly as the real plugin does.
    """

    MISSING_ID = "00000000-0000-0000-0000-00000000dead"

    def _conn(self, monkeypatch, *modules):
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=19999)
        for module in modules:
            monkeypatch.setattr(module, "get_rhino_connection", lambda: conn)
        return conn

    def test_wire_error_carries_code_and_guidance(self, mock_server, monkeypatch):
        conn = self._conn(monkeypatch)
        with pytest.raises(Exception) as info:
            conn.send_command("get_object_info", {"id": self.MISSING_ID})
        text = str(info.value)
        assert text.startswith(f"not_found: Object not found: {self.MISSING_ID}\n")
        assert text.splitlines()[1] == mock_server.OBJECT_NOT_FOUND_GUIDANCE
        assert info.value.code == "not_found"
        # The plugin answered; the socket is still good for the next call.
        assert conn.sock is not None
        assert conn.send_command("get_document_summary")["object_count"] >= 0

    def test_uncoded_error_message_is_unchanged(self, mock_server, monkeypatch):
        conn = self._conn(monkeypatch)
        with pytest.raises(Exception) as info:
            conn.send_command("select_objects", {"filters": {}, "filters_type": "xor"})
        assert str(info.value) == "Invalid filters_type 'xor': expected 'and' or 'or'."
        assert conn.sock is not None

    @pytest.mark.asyncio
    async def test_tool_error_text_for_unknown_object(self, mock_server, monkeypatch):
        import rhinomcp
        import rhinomcp.tools.get_object_info as mod
        from mcp.server.mcpserver.exceptions import ToolError

        self._conn(monkeypatch, mod)
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool("get_object_info", {"id": self.MISSING_ID})
        assert str(info.value) == (
            "Error executing tool get_object_info: "
            f"not_found: Object not found: {self.MISSING_ID}\n"
            f"{mock_server.OBJECT_NOT_FOUND_GUIDANCE}"
        )

    @pytest.mark.asyncio
    async def test_tool_error_text_for_unknown_layer(self, mock_server, monkeypatch):
        import rhinomcp
        import rhinomcp.tools.get_or_set_current_layer as mod
        from mcp.server.mcpserver.exceptions import ToolError

        self._conn(monkeypatch, mod)
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(
                "get_or_set_current_layer", {"name": "NoSuchLayer"}
            )
        assert str(info.value) == (
            "Error executing tool get_or_set_current_layer: "
            "not_found: Layer 'NoSuchLayer' not found\n"
            f"{mock_server.LAYER_NOT_FOUND_GUIDANCE}"
        )

    def test_command_the_plugin_lacks_is_refused_as_unsupported(
        self, mock_server, monkeypatch
    ):
        # The mock does not advertise create_planar_region.
        from rhinomcp.server import PLUGIN_UPDATE_ADVICE

        conn = self._conn(monkeypatch)
        with pytest.raises(Exception) as info:
            conn.send_command("create_planar_region", {"boundary_ids": [self.MISSING_ID]})
        first, guidance = str(info.value).split("\n")
        assert first.startswith(
            f"unsupported: The connected rhinomcp plugin ({mock_server.plugin_version}) "
            "does not "
            "support 'create_planar_region', which was added in plugin 0.4.0;"
        )
        assert guidance == PLUGIN_UPDATE_ADVICE

    def test_parameter_the_plugin_predates_is_refused_as_unsupported(
        self, mock_server, monkeypatch
    ):
        import rhinomcp.server as srv
        from rhinomcp.server import PLUGIN_UPDATE_ADVICE

        # A parameter newer than any plugin, so the mock predates it.
        monkeypatch.setitem(
            srv.PARAMS_SINCE, "sweep1", {"cap_planar_ends": ("99.0.0", False)}
        )
        conn = self._conn(monkeypatch)
        with pytest.raises(Exception) as info:
            conn.send_command(
                "sweep1",
                {"rail_id": self.MISSING_ID, "profile_ids": [self.MISSING_ID],
                 "cap_planar_ends": True},
            )
        assert info.value.code == "unsupported"
        assert str(info.value) == (
            "unsupported: 'sweep1' parameter 'cap_planar_ends' needs plugin 99.0.0; "
            f"the connected rhinomcp plugin ({mock_server.plugin_version}) would "
            "silently ignore it. "
            "The command was not sent.\n"
            f"{PLUGIN_UPDATE_ADVICE} Or call without cap_planar_ends."
        )
        assert "sweep1" not in mock_server.received_commands

    def test_socket_timeout_is_coded(self, monkeypatch):
        import rhinomcp.server as srv

        slow = MockRhinoServer(port=19993)
        slow.response_delay = 0.5
        slow.start()
        try:
            monkeypatch.setattr(srv, "RHINO_TIMEOUT", 0.1)
            conn = srv.RhinoConnection(host="127.0.0.1", port=19993)
            with pytest.raises(Exception) as info:
                conn.send_command("get_document_summary")
            assert info.value.code == "timeout"
            assert str(info.value) == (
                "timeout: Timeout waiting for Rhino response to "
                "'get_document_summary'.\n"
                "Rhino may still be busy: check the document before retrying, "
                "or split the request into smaller steps."
            )
            assert conn.sock is None
        finally:
            slow.stop()

    @pytest.mark.asyncio
    async def test_swallowing_wrapper_now_raises_uncoded_error(
        self, mock_server, monkeypatch
    ):
        import rhinomcp
        import rhinomcp.tools.select_objects as mod
        from mcp.server.mcpserver.exceptions import ToolError

        self._conn(monkeypatch, mod)
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(
                "select_objects", {"filters": {}, "filters_type": "xor"}
            )
        assert str(info.value) == (
            "Error executing tool select_objects: "
            "Invalid filters_type 'xor': expected 'and' or 'or'."
        )


@pytest.fixture
def context_server():
    """A fresh document on its own port, so get_context sees only what a test
    seeds, not what earlier tests left in the module-wide mock."""
    server = MockRhinoServer(port=19996)
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


class TestGetContext:
    """get_context answers a bounded grounding snapshot: every field, the type
    breakdown capped at eight and the selected ids capped at twenty."""

    # Nine types with distinct counts, so the ninth (ARC) falls off the top 8.
    SEED = [("BOX", 9), ("SPHERE", 8), ("CYLINDER", 7), ("CONE", 6), ("LINE", 5),
            ("CIRCLE", 4), ("CURVE", 3), ("POINT", 2), ("ARC", 1)]
    SELECTED_TYPES = ("BOX", "SPHERE", "CYLINDER")  # 9 + 8 + 7 = 24 selected

    def _get_context(self, monkeypatch):
        from rhinomcp.server import RhinoConnection
        import rhinomcp.tools.get_context as context_mod

        conn = RhinoConnection(host="127.0.0.1", port=19996)
        monkeypatch.setattr(context_mod, "get_rhino_connection", lambda: conn)
        return conn, context_mod.get_context

    def _seed(self, server, conn):
        """Two layers with Seat current, 45 objects of nine types, 24 selected.
        Returns the ids of the selected objects. Objects go straight into the
        mock document (the wire would demand real per-type geometry params);
        layer and selection changes go over the wire."""
        conn.send_command("create_layer", {"name": "Seat"})
        conn.send_command("get_or_set_current_layer", {"name": "Seat"})
        ids = {}
        for obj_type, count in self.SEED:
            for i in range(count):
                created = server._create_object({"type": obj_type, "name": f"{obj_type}_{i}"})
                ids[created["name"]] = created["id"]
        names = [n for n in ids if n.split("_")[0] in self.SELECTED_TYPES]
        selected = conn.send_command("select_objects", {"filters": {"name": names}})
        assert selected["count"] == 24
        return {ids[n] for n in names}

    def test_seeded_document(self, context_server, monkeypatch):
        conn, get_context = self._get_context(monkeypatch)
        selected_ids = self._seed(context_server, conn)

        context = get_context(ctx=None)

        assert context["document_name"] == "mock.3dm"
        assert context["document_path"] == "/mock/mock.3dm"
        assert context["units"] == "Millimeters"
        assert context["absolute_tolerance"] == 0.001
        assert context["angle_tolerance"] == 1.0
        assert context["current_layer"] == "Seat"
        assert context["layer_count"] == 2
        assert context["object_count"] == 45
        assert list(context["objects_by_type"].items()) == [
            ("BOX", 9), ("SPHERE", 8), ("CYLINDER", 7), ("CONE", 6),
            ("LINE", 5), ("CIRCLE", 4), ("CURVE", 3), ("POINT", 2),
        ]
        assert context["selection_count"] == 24
        assert len(context["selected_ids"]) == 20
        assert len(set(context["selected_ids"])) == 20
        assert set(context["selected_ids"]) <= selected_ids
        assert context["viewport"] == {
            "name": "Perspective",
            "viewport_name": "Perspective",
            "projection": "perspective",
            "display_mode": "Shaded",
            "camera_location": [100.0, -100.0, 100.0],
            "camera_target": [0.0, 0.0, 0.0],
            "camera_up": [0.0, 0.0, 1.0],
            "lens_length": 50.0,
        }
        assert context["scene_bounding_box"] == {"min": [-1, -1, -1], "max": [1, 1, 1]}
        assert context["grasshopper_definition_count"] == 0
        assert "layer_hierarchy" not in context
        assert "objects_by_layer" not in context

    @pytest.mark.asyncio
    async def test_typical_model_stays_under_sixty_lines(self, context_server, monkeypatch):
        """Measured on the text the client receives, not on the dict."""
        import rhinomcp

        conn, _ = self._get_context(monkeypatch)
        for obj_type, count in [("BREP", 30), ("CURVE", 12), ("EXTRUSION", 6), ("MESH", 2)]:
            for i in range(count):
                context_server._create_object({"type": obj_type, "name": f"{obj_type}_{i}"})
        conn.send_command("select_objects", {"filters": {"name": ["BREP_0", "BREP_1", "MESH_0"]}})

        result = await rhinomcp.mcp.call_tool("get_context", {})

        text = result.content[0].text
        assert json.loads(text)["selection_count"] == 3
        assert len(text.splitlines()) < 60

    def test_empty_document(self, context_server, monkeypatch):
        _, get_context = self._get_context(monkeypatch)

        context = get_context(ctx=None)

        assert context["object_count"] == 0
        assert context["objects_by_type"] == {}
        assert context["selection_count"] == 0
        assert context["selected_ids"] == []
        assert context["scene_bounding_box"] is None
        assert context["current_layer"] == "Default"
        assert context["layer_count"] == 1

    def test_reading_context_changes_nothing(self, context_server, monkeypatch):
        _, get_context = self._get_context(monkeypatch)
        context_server._create_object({"type": "BOX", "name": "Only"})
        before = json.dumps(context_server.objects, sort_keys=True)
        undo_before = list(context_server.undo_stack)

        get_context(ctx=None)

        assert json.dumps(context_server.objects, sort_keys=True) == before
        assert context_server.undo_stack == undo_before

    @pytest.mark.asyncio
    async def test_tool_is_annotated_read_only(self):
        import rhinomcp

        tool = next(t for t in await rhinomcp.mcp.list_tools() if t.name == "get_context")
        assert tool.annotations.title == "Get context"
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.open_world_hint is False


@pytest.fixture
def filter_server():
    """A fresh seeded document on its own port, so filter tests see exactly
    the five objects they seed and nothing earlier tests left behind."""
    server = MockRhinoServer(port=19975)
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


class _FilterDocument:
    """Five objects over two layers, one hidden and one locked:

    ===========  ======  =======  ===========
    name         type    layer    state
    ===========  ======  =======  ===========
    box_default  BOX     Default  normal
    box_walls    BOX     Walls    normal
    curve_walls  CURVE   Walls    hidden
    sphere_lock  SPHERE  Default  locked
    curve_red    CURVE   Default  normal, red
    ===========  ======  =======  ===========
    """

    def _connect(self, monkeypatch, server):
        import rhinomcp.tools.get_objects as get_mod
        import rhinomcp.tools.select_objects as select_mod
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=server.port)
        for module in (get_mod, select_mod):
            monkeypatch.setattr(module, "get_rhino_connection", lambda: conn)
        return conn

    def _seed(self, server, monkeypatch):
        conn = self._connect(monkeypatch, server)
        conn.send_command("create_layer", {"name": "Walls"})
        ids = {}

        def add(name, obj_type, layer, **state):
            server.current_layer = layer
            obj = server._create_object({"type": obj_type, "name": name})
            obj.update(state)
            ids[name] = obj["id"]

        add("box_default", "BOX", "Default")
        add("box_walls", "BOX", "Walls")
        add("curve_walls", "CURVE", "Walls", visible=False)
        add("sphere_lock", "SPHERE", "Default", locked=True)
        add("curve_red", "CURVE", "Default", color={"r": 255, "g": 0, "b": 0})
        server.current_layer = "Default"
        return conn, ids

    @staticmethod
    def _selected(server, ids):
        by_id = {v: k for k, v in ids.items()}
        return sorted(by_id[i] for i in server.selected_ids)


class TestSelectionFilters(_FilterDocument):
    """select_objects honours ids, layer, type, hidden and locked alone and
    combined with name and color under the and/or rule, through the tool."""

    async def _select(self, filters, filters_type="and"):
        import rhinomcp

        result = await rhinomcp.mcp.call_tool(
            "select_objects", {"filters": filters, "filters_type": filters_type}
        )
        return result.content[0].text

    @pytest.mark.asyncio
    async def test_ids_alone(self, filter_server, monkeypatch):
        _, ids = self._seed(filter_server, monkeypatch)
        text = await self._select({"ids": [ids["box_walls"], ids["curve_red"]]})
        assert text == "Selected 2 objects"
        assert self._selected(filter_server, ids) == ["box_walls", "curve_red"]

    @pytest.mark.asyncio
    async def test_layer_alone(self, filter_server, monkeypatch):
        _, ids = self._seed(filter_server, monkeypatch)
        await self._select({"layer": "Walls"})
        # curve_walls is hidden, so it is not a candidate unless asked for.
        assert self._selected(filter_server, ids) == ["box_walls"]

    @pytest.mark.asyncio
    async def test_type_as_string_and_as_list(self, filter_server, monkeypatch):
        _, ids = self._seed(filter_server, monkeypatch)
        await self._select({"type": "CURVE"})
        assert self._selected(filter_server, ids) == ["curve_red"]
        await self._select({"type": ["BOX", "SPHERE"]})
        assert self._selected(filter_server, ids) == ["box_default", "box_walls"]

    @pytest.mark.asyncio
    async def test_hidden_true_matches_but_is_not_selectable(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        text = await self._select({"hidden": True})
        assert text == (
            "Selected 0 objects (1 matched; 1 hidden or locked and Rhino cannot "
            "select them: show or unlock them first)"
        )
        assert self._selected(filter_server, ids) == []

    @pytest.mark.asyncio
    async def test_locked_true_matches_but_is_not_selectable(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        text = await self._select({"locked": True})
        assert text.startswith("Selected 0 objects (1 matched; 1 hidden or locked")

    @pytest.mark.asyncio
    async def test_hidden_false_and_locked_false(self, filter_server, monkeypatch):
        _, ids = self._seed(filter_server, monkeypatch)
        normal = ["box_default", "box_walls", "curve_red"]
        await self._select({"hidden": False})
        assert self._selected(filter_server, ids) == normal
        await self._select({"locked": False})
        assert self._selected(filter_server, ids) == normal

    @pytest.mark.asyncio
    async def test_and_combines_new_and_existing_filters(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        await self._select({"layer": "Default", "type": "BOX"})
        assert self._selected(filter_server, ids) == ["box_default"]
        await self._select({"type": "CURVE", "color": [255, 0, 0], "locked": False})
        assert self._selected(filter_server, ids) == ["curve_red"]
        await self._select(
            {"ids": [ids["box_default"], ids["box_walls"]], "name": ["box_walls"]}
        )
        assert self._selected(filter_server, ids) == ["box_walls"]

    @pytest.mark.asyncio
    async def test_or_combines_new_and_existing_filters(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        await self._select({"layer": "Walls", "name": ["box_default"]}, "or")
        assert self._selected(filter_server, ids) == ["box_default", "box_walls"]
        await self._select(
            {"ids": [ids["curve_red"]], "type": "BOX", "color": [9, 9, 9]}, "or"
        )
        assert self._selected(filter_server, ids) == [
            "box_default", "box_walls", "curve_red",
        ]

    @pytest.mark.asyncio
    async def test_empty_and_name_filters_skip_hidden_and_locked(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        text = await self._select({"name": ["box_default", "sphere_lock"]})
        assert text == "Selected 1 objects"
        await self._select({})
        assert self._selected(filter_server, ids) == [
            "box_default", "box_walls", "curve_red",
        ]


class TestListingFilters(_FilterDocument):
    """get_objects lists by ids, the current selection, and optionally hidden
    or locked objects; the defaults list what they listed before 0.5.0."""

    async def _list(self, **arguments):
        import rhinomcp

        result = await rhinomcp.mcp.call_tool("get_objects", arguments)
        listing = json.loads(result.content[0].text)
        names = sorted(o["name"] for o in listing["objects"])
        assert listing["total_matching"] == len(names)
        return names

    @pytest.mark.asyncio
    async def test_defaults_list_locked_but_not_hidden(self, filter_server, monkeypatch):
        self._seed(filter_server, monkeypatch)
        assert await self._list() == [
            "box_default", "box_walls", "curve_red", "sphere_lock",
        ]

    @pytest.mark.asyncio
    async def test_include_hidden(self, filter_server, monkeypatch):
        self._seed(filter_server, monkeypatch)
        assert await self._list(include_hidden=True) == [
            "box_default", "box_walls", "curve_red", "curve_walls", "sphere_lock",
        ]

    @pytest.mark.asyncio
    async def test_exclude_locked(self, filter_server, monkeypatch):
        self._seed(filter_server, monkeypatch)
        assert await self._list(include_locked=False) == [
            "box_default", "box_walls", "curve_red",
        ]

    @pytest.mark.asyncio
    async def test_ids_restrict_and_unknown_ids_are_absent(
        self, filter_server, monkeypatch
    ):
        _, ids = self._seed(filter_server, monkeypatch)
        missing = "00000000-0000-0000-0000-00000000dead"
        names = await self._list(ids=[ids["box_walls"], ids["curve_walls"], missing])
        # curve_walls is hidden, so ids alone do not bring it in.
        assert names == ["box_walls"]
        names = await self._list(
            ids=[ids["box_walls"], ids["curve_walls"]], include_hidden=True
        )
        assert names == ["box_walls", "curve_walls"]

    @pytest.mark.asyncio
    async def test_selected_only(self, filter_server, monkeypatch):
        conn, ids = self._seed(filter_server, monkeypatch)
        conn.send_command(
            "select_objects", {"filters": {"name": ["box_walls", "curve_red"]}}
        )
        assert await self._list(selected_only=True) == ["box_walls", "curve_red"]
        assert await self._list(selected_only=True, type_filter="curve") == ["curve_red"]

    @pytest.mark.asyncio
    async def test_selected_only_with_nothing_selected(self, filter_server, monkeypatch):
        self._seed(filter_server, monkeypatch)
        assert await self._list(selected_only=True) == []

    @pytest.mark.asyncio
    async def test_combined_with_layer_filter(self, filter_server, monkeypatch):
        _, ids = self._seed(filter_server, monkeypatch)
        names = await self._list(layer_filter="Walls", include_hidden=True)
        assert names == ["box_walls", "curve_walls"]
        names = await self._list(
            layer_filter="Default", include_locked=False,
            ids=[ids["sphere_lock"], ids["box_default"]],
        )
        assert names == ["box_default"]


class TestFilterRefusals(_FilterDocument):
    """An unknown layer in either tool, or an unknown id in a selection
    filter, is refused with not_found and guidance, and selects nothing."""

    MISSING_ID = "00000000-0000-0000-0000-00000000dead"

    @pytest.mark.asyncio
    async def test_select_unknown_layer(self, filter_server, monkeypatch):
        import rhinomcp
        from mcp.server.mcpserver.exceptions import ToolError

        conn, ids = self._seed(filter_server, monkeypatch)
        conn.send_command("select_objects", {"filters": {"name": ["box_default"]}})
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(
                "select_objects", {"filters": {"layer": "NoSuchLayer"}}
            )
        assert str(info.value) == (
            "Error executing tool select_objects: "
            "not_found: Layer 'NoSuchLayer' not found\n"
            f"{filter_server.LAYER_NOT_FOUND_GUIDANCE}"
        )
        # Refused before touching the selection.
        assert self._selected(filter_server, ids) == ["box_default"]

    @pytest.mark.asyncio
    async def test_select_unknown_id(self, filter_server, monkeypatch):
        import rhinomcp
        from mcp.server.mcpserver.exceptions import ToolError

        _, ids = self._seed(filter_server, monkeypatch)
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(
                "select_objects",
                {"filters": {"ids": [ids["box_walls"], self.MISSING_ID]},
                 "filters_type": "or"},
            )
        assert str(info.value) == (
            "Error executing tool select_objects: "
            f"not_found: Object not found: {self.MISSING_ID}\n"
            f"{filter_server.OBJECT_NOT_FOUND_GUIDANCE}"
        )

    @pytest.mark.asyncio
    async def test_list_unknown_layer_lists_nothing(self, filter_server, monkeypatch):
        # Agents list a layer they are about to create; a read-only listing of an
        # absent layer is empty, not an error (0.5.0 refused; reverted in 0.5.1).
        import rhinomcp

        self._seed(filter_server, monkeypatch)
        result = await rhinomcp.mcp.call_tool("get_objects", {"layer_filter": "NoSuchLayer"})
        listing = json.loads(result.content[0].text)
        assert listing["objects"] == []
        assert listing["total_matching"] == 0


@pytest.fixture
def plugin_041_server():
    """A 0.4.1 plugin, which would read the new filter keys as custom
    attributes and ignore the new listing parameters."""
    server = MockRhinoServer(port=19976, plugin_version="0.4.1")
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


class TestFilterPluginCompatibility(_FilterDocument):
    """Against a plugin older than 0.5.0 the new filters are refused with
    update advice before anything is sent; the defaults still go through."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool, arguments, name", [
        ("select_objects", {"filters": {"ids": ["00000000-0000-0000-0000-000000000001"]}}, "filters.ids"),
        ("select_objects", {"filters": {"layer": "Walls"}}, "filters.layer"),
        ("select_objects", {"filters": {"type": "CURVE"}, "filters_type": "or"}, "filters.type"),
        ("select_objects", {"filters": {"hidden": False}}, "filters.hidden"),
        ("select_objects", {"filters": {"locked": False}}, "filters.locked"),
        ("get_objects", {"ids": ["00000000-0000-0000-0000-000000000001"]}, "ids"),
        ("get_objects", {"selected_only": True}, "selected_only"),
        ("get_objects", {"include_hidden": True}, "include_hidden"),
        ("get_objects", {"include_locked": False}, "include_locked"),
    ])
    async def test_new_parameter_refused_with_update_advice(
        self, plugin_041_server, monkeypatch, tool, arguments, name
    ):
        import rhinomcp
        from mcp.server.mcpserver.exceptions import ToolError
        from rhinomcp.server import PLUGIN_UPDATE_ADVICE

        self._seed(plugin_041_server, monkeypatch)
        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(tool, arguments)
        assert str(info.value) == (
            f"Error executing tool {tool}: "
            f"unsupported: '{tool}' parameter '{name}' needs plugin 0.5.0; "
            "the connected rhinomcp plugin (0.4.1) would silently ignore it. "
            "The command was not sent.\n"
            f"{PLUGIN_UPDATE_ADVICE} Or call without {name}."
        )
        assert tool not in plugin_041_server.received_commands

    @pytest.mark.asyncio
    async def test_existing_filters_and_defaults_still_work(
        self, plugin_041_server, monkeypatch
    ):
        import rhinomcp

        self._seed(plugin_041_server, monkeypatch)
        selected = await rhinomcp.mcp.call_tool(
            "select_objects", {"filters": {"name": ["box_default"], "category": ["x"]},
                               "filters_type": "or"}
        )
        assert selected.content[0].text == "Selected 1 objects"
        listed = await rhinomcp.mcp.call_tool(
            "get_objects", {"include_hidden": False, "include_locked": True}
        )
        assert json.loads(listed.content[0].text)["total_matching"] == 4


@pytest.fixture
def capture_server():
    """A fresh document on its own port, so capture metadata counts only what a
    test seeds."""
    server = MockRhinoServer(port=19980)
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


@pytest.fixture
def camera_server():
    """A fresh document and fresh viewports on their own port, so camera tests
    see only the objects and view changes they make."""
    server = MockRhinoServer(port=19985)
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


class TestCaptureViewportMetadata:
    """capture_viewport answers a content list: the image, then a text block
    with a JSON object saying what the image shows."""

    METADATA_KEYS = {
        "viewport_name", "display_mode", "projection", "width", "height",
        "camera_location", "camera_target", "camera_up", "lens_length",
        "scene_bounding_box", "visible_object_count", "total_object_count",
    }

    def _connect(self, monkeypatch, port=19980):
        from rhinomcp.server import RhinoConnection
        import rhinomcp.tools.capture_viewport as capture_mod

        conn = RhinoConnection(host="127.0.0.1", port=port)
        monkeypatch.setattr(capture_mod, "get_rhino_connection", lambda: conn)
        return conn

    async def _capture(self, **arguments):
        import rhinomcp

        return await rhinomcp.mcp.call_tool("capture_viewport", arguments)

    @pytest.mark.asyncio
    async def test_default_capture_is_png_then_metadata(self, capture_server, monkeypatch):
        import base64

        self._connect(monkeypatch)
        capture_server._create_object({"type": "BOX", "name": "A"})
        capture_server._create_object({"type": "SPHERE", "name": "B"})

        result = await self._capture()

        image, text = result.content
        assert image.type == "image"
        assert image.mime_type == "image/png"
        assert base64.b64decode(image.data).startswith(b"\x89PNG\r\n\x1a\n")
        assert text.type == "text"
        metadata = json.loads(text.text)
        assert set(metadata) == self.METADATA_KEYS
        assert metadata == {
            "viewport_name": "Perspective",
            "display_mode": "Shaded",
            "projection": "perspective",
            "width": 800,
            "height": 600,
            "camera_location": [100.0, -100.0, 100.0],
            "camera_target": [0.0, 0.0, 0.0],
            "camera_up": [0.0, 0.0, 1.0],
            "lens_length": 50.0,
            "scene_bounding_box": {"min": [-1, -1, -1], "max": [1, 1, 1]},
            "visible_object_count": 2,
            "total_object_count": 2,
        }

    @pytest.mark.asyncio
    async def test_empty_document_has_null_bounding_box(self, capture_server, monkeypatch):
        self._connect(monkeypatch)

        result = await self._capture()

        metadata = json.loads(result.content[1].text)
        assert metadata["scene_bounding_box"] is None
        assert metadata["visible_object_count"] == 0
        assert metadata["total_object_count"] == 0

    @pytest.mark.asyncio
    async def test_jpeg_format_returns_jpeg_image(self, capture_server, monkeypatch):
        import base64

        self._connect(monkeypatch)

        result = await self._capture(format="jpeg")

        image = result.content[0]
        assert image.mime_type == "image/jpeg"
        assert base64.b64decode(image.data).startswith(b"\xff\xd8\xff")
        assert capture_server.received_params["capture_viewport"]["format"] == "jpeg"

    @pytest.mark.asyncio
    async def test_display_mode_and_camera_reach_the_plugin(self, capture_server, monkeypatch):
        self._connect(monkeypatch)

        result = await self._capture(
            display_mode="Wireframe",
            camera_location=[10, -20, 30],
            camera_target=[1, 2, 3],
            lens_length=35,
        )

        sent = capture_server.received_params["capture_viewport"]
        assert sent["display_mode"] == "Wireframe"
        assert sent["camera_location"] == [10, -20, 30]
        assert sent["camera_target"] == [1, 2, 3]
        assert sent["lens_length"] == 35
        assert "frame_object_ids" not in sent and "frame_bbox" not in sent
        metadata = json.loads(result.content[1].text)
        assert metadata["display_mode"] == "Wireframe"
        assert metadata["camera_location"] == [10, -20, 30]
        assert metadata["camera_target"] == [1, 2, 3]
        assert metadata["lens_length"] == 35

    @pytest.mark.asyncio
    async def test_framing_targets_reach_the_plugin(self, capture_server, monkeypatch):
        self._connect(monkeypatch)
        box = capture_server._create_object({"type": "BOX", "name": "A"})

        await self._capture(frame_object_ids=[box["id"]])
        assert capture_server.received_params["capture_viewport"]["frame_object_ids"] == [box["id"]]

        bbox = {"min": [0, 0, 0], "max": [5, 5, 5]}
        result = await self._capture(frame_bbox=bbox)
        assert capture_server.received_params["capture_viewport"]["frame_bbox"] == bbox
        # Framing looks at the middle of the box.
        assert json.loads(result.content[1].text)["camera_target"] == [2.5, 2.5, 2.5]

    @pytest.mark.asyncio
    async def test_temporary_camera_leaves_the_viewport_as_it_was(
        self, capture_server, monkeypatch
    ):
        conn = self._connect(monkeypatch)
        before = conn.send_command("get_context")["viewport"]

        await self._capture(display_mode="Wireframe", camera_location=[9, 9, 9],
                            camera_target=[1, 1, 1])
        await self._capture(frame_bbox={"min": [0, 0, 0], "max": [2, 2, 2]})

        assert conn.send_command("get_context")["viewport"] == before

    async def _refusal(self, **arguments):
        from mcp.server.mcpserver.exceptions import ToolError

        with pytest.raises(ToolError) as info:
            await self._capture(**arguments)
        prefix = "Error executing tool capture_viewport: "
        assert str(info.value).startswith(prefix)
        return str(info.value)[len(prefix):]

    @pytest.mark.asyncio
    async def test_camera_plus_framing_is_refused(self, capture_server, monkeypatch):
        self._connect(monkeypatch)
        box = capture_server._create_object({"type": "BOX", "name": "A"})

        for camera in ({"camera_location": [9, 9, 9]}, {"camera_target": [0, 0, 0]},
                       {"lens_length": 35}):
            for framing in ({"frame_object_ids": [box["id"]]},
                            {"frame_bbox": {"min": [0, 0, 0], "max": [1, 1, 1]}},
                            {"zoom_to_fit": True}):
                text = await self._refusal(**camera, **framing)
                assert text == (
                    "invalid_argument: An explicit camera (camera_location, "
                    "camera_target, lens_length) cannot be combined with framing "
                    "(frame_object_ids, frame_bbox, zoom_to_fit)\n"
                    "Pass camera_location, camera_target or lens_length to look "
                    "from a known point, or frame_object_ids, frame_bbox or "
                    "zoom_to_fit to frame geometry, not both."
                )

    @pytest.mark.asyncio
    async def test_camera_with_zoom_to_fit_off_is_not_refused(self, capture_server, monkeypatch):
        self._connect(monkeypatch)

        result = await self._capture(camera_location=[9, 9, 9], lens_length=35, zoom_to_fit=False)

        assert result.content[0].type == "image"

    @pytest.mark.asyncio
    async def test_unknown_display_mode_lists_the_available_modes(
        self, capture_server, monkeypatch
    ):
        self._connect(monkeypatch)

        text = await self._refusal(display_mode="Cartoon")

        message, guidance = text.split("\n")
        assert message == "invalid_argument: Display mode 'Cartoon' not found"
        assert guidance == (
            "Use one of the available display modes: Wireframe, Shaded, Rendered, "
            "Ghosted, X-Ray, Technical, Artistic, Pen, Arctic, Raytraced."
        )

    @pytest.mark.asyncio
    async def test_unknown_frame_object_is_not_found(self, capture_server, monkeypatch):
        self._connect(monkeypatch)
        missing = "00000000-0000-0000-0000-00000000dead"

        text = await self._refusal(frame_object_ids=[missing])

        assert text == (
            f"not_found: Object not found: {missing}\n"
            f"{capture_server.OBJECT_NOT_FOUND_GUIDANCE}"
        )

    @pytest.mark.asyncio
    async def test_plugin_older_than_050_refuses_the_new_params(self, monkeypatch):
        from rhinomcp.server import PLUGIN_UPDATE_ADVICE

        old = MockRhinoServer(port=19981, plugin_version="0.4.1")
        old.start()
        try:
            self._connect(monkeypatch, port=19981)
            new_params = {
                "display_mode": "Wireframe",
                "camera_location": [1, 1, 1],
                "camera_target": [0, 0, 0],
                "lens_length": 35,
                "frame_object_ids": ["00000000-0000-0000-0000-00000000dead"],
                "frame_bbox": {"min": [0, 0, 0], "max": [1, 1, 1]},
                "format": "jpeg",
            }
            for name, value in new_params.items():
                text = await self._refusal(**{name: value})
                assert text == (
                    f"unsupported: 'capture_viewport' parameter '{name}' needs plugin "
                    "0.5.0; the connected rhinomcp plugin (0.4.1) would silently "
                    "ignore it. The command was not sent.\n"
                    f"{PLUGIN_UPDATE_ADVICE} Or call without {name}."
                )
            assert "capture_viewport" not in old.received_commands

            # The defaults are what an old plugin already does, so they still go through.
            result = await self._capture(format="png")
            assert result.content[0].mime_type == "image/png"
            assert "format" in old.received_params["capture_viewport"]
        finally:
            old.stop()


class TestCameraTools:
    """set_camera and zoom_to change a viewport (named or active), answer its
    state afterwards, and leave the document and its undo stack alone."""

    PORT = 19985
    MISSING_ID = "00000000-0000-0000-0000-00000000dead"

    def _tools(self, monkeypatch):
        from rhinomcp.server import RhinoConnection
        import rhinomcp.tools.set_camera as set_camera_mod
        import rhinomcp.tools.get_context as context_mod

        conn = RhinoConnection(host="127.0.0.1", port=self.PORT)
        for mod in (set_camera_mod, context_mod):
            monkeypatch.setattr(mod, "get_rhino_connection", lambda: conn)
        return conn

    async def _refusal(self, tool, args):
        """The tool error text after the SDK's own 'Error executing tool' prefix."""
        import rhinomcp
        from mcp.server.mcpserver.exceptions import ToolError

        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(tool, args)
        prefix = f"Error executing tool {tool}: "
        text = str(info.value)
        assert text.startswith(prefix)
        return text[len(prefix):]

    # set_camera

    def test_set_camera_updates_the_active_viewport(self, camera_server, monkeypatch):
        from rhinomcp.tools.set_camera import set_camera
        from rhinomcp.tools.get_context import get_context

        self._tools(monkeypatch)
        undo_before = list(camera_server.undo_stack)

        state = set_camera(ctx=None, location=[10, -20, 30], target=[1, 2, 3],
                           up=[0, 1, 0], lens_length=35)

        assert state == {
            "viewport_name": "Perspective",
            "projection": "perspective",
            "display_mode": "Shaded",
            "camera_location": [10, -20, 30],
            "camera_target": [1, 2, 3],
            "camera_up": [0, 1, 0],
            "lens_length": 35,
        }
        viewport = get_context(ctx=None)["viewport"]
        assert viewport["camera_location"] == [10, -20, 30]
        assert viewport["camera_target"] == [1, 2, 3]
        assert camera_server.undo_stack == undo_before

    def test_set_camera_on_a_named_viewport_leaves_the_active_one(
        self, camera_server, monkeypatch
    ):
        from rhinomcp.tools.set_camera import set_camera
        from rhinomcp.tools.get_context import get_context

        self._tools(monkeypatch)
        active_before = get_context(ctx=None)["viewport"]

        state = set_camera(ctx=None, viewport="Top", projection="perspective",
                           lens_length=80)

        assert state["viewport_name"] == "Top"
        assert state["projection"] == "perspective"
        assert state["lens_length"] == 80
        # Fields not given keep their previous values.
        assert state["camera_target"] == [0.0, 0.0, 0.0]
        assert state["camera_up"] == [0.0, 1.0, 0.0]
        assert get_context(ctx=None)["viewport"] == active_before

    def test_set_camera_switches_to_parallel(self, camera_server, monkeypatch):
        from rhinomcp.tools.set_camera import set_camera

        self._tools(monkeypatch)
        assert set_camera(ctx=None, projection="parallel")["projection"] == "parallel"

    @pytest.mark.asyncio
    async def test_set_camera_with_nothing_to_change_is_refused(
        self, camera_server, monkeypatch
    ):
        self._tools(monkeypatch)
        text = await self._refusal("set_camera", {"viewport": "Top"})
        assert text == (
            "invalid_argument: set_camera needs at least one of location, target, "
            "up, lens_length or projection\n"
            "Pass the camera fields to change; to frame objects use zoom_to instead."
        )

    @pytest.mark.asyncio
    async def test_set_camera_on_an_unknown_viewport_is_refused(
        self, camera_server, monkeypatch
    ):
        self._tools(monkeypatch)
        text = await self._refusal("set_camera", {"viewport": "Nowhere", "lens_length": 50})
        assert text == (
            "not_found: Viewport 'Nowhere' not found\n"
            "Omit viewport to use the active one, or pass a viewport name such as "
            "Perspective, Top, Front or Right."
        )

    @pytest.mark.asyncio
    async def test_set_camera_is_annotated_as_a_view_change(self):
        import rhinomcp

        tool = next(t for t in await rhinomcp.mcp.list_tools() if t.name == "set_camera")
        assert tool.annotations.title == "Set camera"
        assert tool.annotations.read_only_hint is False
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.open_world_hint is False

    # zoom_to

    def _zoom_tools(self, monkeypatch):
        import rhinomcp.tools.zoom_to as zoom_to_mod
        import rhinomcp.tools.select_objects as select_mod

        conn = self._tools(monkeypatch)
        for mod in (zoom_to_mod, select_mod):
            monkeypatch.setattr(mod, "get_rhino_connection", lambda: conn)
        return conn

    def _box(self, server, name, lo, hi, layer=None):
        """An object with a known bounding box, straight into the mock document."""
        created = server._create_object({"type": "BOX", "name": name})
        server.objects[created["id"]]["bounding_box"] = [lo, hi]
        if layer:
            server.objects[created["id"]]["layer"] = layer
        return created["id"]

    def _two_boxes(self, server):
        a = self._box(server, "a", [0, 0, 0], [2, 2, 2])
        b = self._box(server, "b", [8, 10, 4], [10, 20, 6])
        return a, b

    def test_zoom_to_all_frames_every_object(self, camera_server, monkeypatch):
        from rhinomcp.tools.zoom_to import zoom_to

        self._zoom_tools(monkeypatch)
        self._two_boxes(camera_server)
        undo_before = list(camera_server.undo_stack)

        state = zoom_to(ctx=None, target="all")

        assert state["viewport_name"] == "Perspective"
        assert state["bounding_box"] == {"min": [0, 0, 0], "max": [10, 20, 6]}
        assert state["object_count"] == 2
        assert state["camera_target"] == [5.0, 10.0, 3.0]
        assert set(state) >= {"projection", "camera_location", "camera_up", "lens_length"}
        assert camera_server.undo_stack == undo_before

    def test_zoom_to_selection_in_a_named_viewport(self, camera_server, monkeypatch):
        from rhinomcp.tools.select_objects import select_objects
        from rhinomcp.tools.zoom_to import zoom_to

        self._zoom_tools(monkeypatch)
        self._two_boxes(camera_server)
        select_objects(ctx=None, filters={"name": ["b"]})

        state = zoom_to(ctx=None, target="selection", viewport="Top")

        assert state["viewport_name"] == "Top"
        assert state["projection"] == "parallel"
        assert state["bounding_box"] == {"min": [8, 10, 4], "max": [10, 20, 6]}
        assert state["object_count"] == 1
        assert state["camera_target"] == [9.0, 15.0, 5.0]

    def test_zoom_to_object_ids(self, camera_server, monkeypatch):
        from rhinomcp.tools.zoom_to import zoom_to

        self._zoom_tools(monkeypatch)
        a, _ = self._two_boxes(camera_server)
        c = self._box(camera_server, "c", [-4, 0, 0], [0, 1, 1])

        state = zoom_to(ctx=None, target="object_ids", object_ids=[a, c])

        assert state["bounding_box"] == {"min": [-4, 0, 0], "max": [2, 2, 2]}
        assert state["object_count"] == 2

    def test_zoom_to_layer(self, camera_server, monkeypatch):
        from rhinomcp.tools.zoom_to import zoom_to

        conn = self._zoom_tools(monkeypatch)
        conn.send_command("create_layer", {"name": "Legs"})
        self._box(camera_server, "seat", [0, 0, 0], [2, 2, 2])
        self._box(camera_server, "leg1", [0, 0, -10], [1, 1, 0], layer="Legs")
        self._box(camera_server, "leg2", [5, 5, -10], [6, 6, 0], layer="Legs")

        state = zoom_to(ctx=None, target="layer", layer="Legs")

        assert state["bounding_box"] == {"min": [0, 0, -10], "max": [6, 6, 0]}
        assert state["object_count"] == 2

    @pytest.mark.asyncio
    async def test_zoom_to_unknown_object_ids_is_refused(self, camera_server, monkeypatch):
        self._zoom_tools(monkeypatch)
        a, _ = self._two_boxes(camera_server)
        text = await self._refusal(
            "zoom_to", {"target": "object_ids", "object_ids": [a, self.MISSING_ID]}
        )
        assert text == (
            f"not_found: Object not found: {self.MISSING_ID}\n"
            "Call get_objects or get_selected_objects_info to find a valid object "
            "id or name."
        )

    @pytest.mark.asyncio
    async def test_zoom_to_unknown_layer_is_refused(self, camera_server, monkeypatch):
        self._zoom_tools(monkeypatch)
        text = await self._refusal("zoom_to", {"target": "layer", "layer": "NoSuchLayer"})
        assert text == (
            "not_found: Layer 'NoSuchLayer' not found\n"
            "Call get_document_summary to list existing layers, or create_layer to "
            "make it first."
        )

    @pytest.mark.asyncio
    async def test_zoom_to_empty_selection_is_refused(self, camera_server, monkeypatch):
        self._zoom_tools(monkeypatch)
        self._two_boxes(camera_server)
        text = await self._refusal("zoom_to", {"target": "selection"})
        assert text == (
            "invalid_argument: Nothing is selected to zoom to\n"
            "Select objects first with select_objects, or use target 'all', "
            "'object_ids' or 'layer'."
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("target", ["object_ids", "layer"])
    async def test_zoom_to_without_its_companion_field_is_refused(
        self, camera_server, monkeypatch, target
    ):
        self._zoom_tools(monkeypatch)
        text = await self._refusal("zoom_to", {"target": target})
        assert text == (
            f"invalid_argument: target '{target}' needs {target}\n"
            f"Pass {target}, or use target 'all' or 'selection'."
        )

    @pytest.mark.asyncio
    async def test_zoom_to_unknown_viewport_is_refused(self, camera_server, monkeypatch):
        self._zoom_tools(monkeypatch)
        self._two_boxes(camera_server)
        text = await self._refusal("zoom_to", {"target": "all", "viewport": "Nowhere"})
        assert text == (
            "not_found: Viewport 'Nowhere' not found\n"
            "Omit viewport to use the active one, or pass a viewport name such as "
            "Perspective, Top, Front or Right."
        )

    @pytest.mark.asyncio
    async def test_zoom_to_is_annotated_as_a_view_change(self):
        import rhinomcp

        tool = next(t for t in await rhinomcp.mcp.list_tools() if t.name == "zoom_to")
        assert tool.annotations.title == "Zoom to"
        assert tool.annotations.read_only_hint is False
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.open_world_hint is False

    @pytest.mark.parametrize("command,params", [
        ("set_camera", {"lens_length": 50}),
        ("zoom_to", {"target": "all"}),
    ])
    def test_a_0_4_1_plugin_refuses_camera_commands_with_advice(self, command, params):
        from rhinomcp.server import RhinoConnection

        server = MockRhinoServer(port=19986, plugin_version="0.4.1")
        server.start()
        time.sleep(0.1)
        try:
            conn = RhinoConnection(host="127.0.0.1", port=19986)
            with pytest.raises(Exception) as info:
                conn.send_command(command, params)
            conn.disconnect()
        finally:
            server.stop()

        assert info.value.code == "unsupported"
        assert str(info.value).startswith(
            "unsupported: The connected rhinomcp plugin (0.4.1) does not support "
            f"'{command}', which was added in plugin 0.5.0;"
        )
        assert command not in server.received_commands


@pytest.fixture
def undo_group_server():
    """A 0.6.0 plugin with an empty undo stack, on its own port."""
    server = MockRhinoServer(port=19974, plugin_version="0.6.0")
    server.start()
    time.sleep(0.1)

    yield server

    server.stop()


class TestUndoGroups:
    """Changes made between begin_undo_group and end_undo_group revert with one
    undo. Groups do not nest, undo is refused inside one, and a group ends with
    the client that began it."""

    PORT = 19974
    BOX = {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}}

    def _connection(self):
        from rhinomcp.server import RhinoConnection

        return RhinoConnection(host="127.0.0.1", port=self.PORT)

    def _tools(self, monkeypatch):
        import rhinomcp.tools.undo as undo_mod
        import rhinomcp.tools.undo_group as undo_group_mod

        conn = self._connection()
        for mod in (undo_mod, undo_group_mod):
            monkeypatch.setattr(mod, "get_rhino_connection", lambda: conn)
        return conn

    async def _refusal(self, tool, args):
        """The tool error text after the SDK's own 'Error executing tool' prefix."""
        import rhinomcp
        from mcp.server.mcpserver.exceptions import ToolError

        with pytest.raises(ToolError) as info:
            await rhinomcp.mcp.call_tool(tool, args)
        prefix = f"Error executing tool {tool}: "
        text = str(info.value)
        assert text.startswith(prefix)
        return text[len(prefix):]

    def test_one_undo_reverts_every_change_in_the_group(
        self, undo_group_server, monkeypatch
    ):
        from rhinomcp.tools.undo import undo
        from rhinomcp.tools.undo_group import begin_undo_group, end_undo_group

        conn = self._tools(monkeypatch)
        begun = begin_undo_group(ctx=None, name="Build three boxes")
        for i in range(3):
            conn.send_command("create_object", {**self.BOX, "name": f"Box{i}"})
        ended = end_undo_group(ctx=None)

        assert begun["undo_description"] == "MCP: Build three boxes"
        assert begun["idle_timeout_seconds"] == 120
        assert ended["ended"] is True
        assert ended["end_reason"] == "requested"
        assert ended["command_count"] == 3
        assert undo(ctx=None, steps=1) == "Undid 1 operation(s)"
        assert undo(ctx=None, steps=1) == "Nothing to undo"
        conn.disconnect()

    @pytest.mark.asyncio
    async def test_groups_do_not_nest(self, undo_group_server, monkeypatch):
        conn = self._tools(monkeypatch)
        await self._call("begin_undo_group", {"name": "Outer"})

        text = await self._refusal("begin_undo_group", {"name": "Inner"})

        assert text == (
            "invalid_argument: Undo group 'Outer' is already open\n"
            "Undo groups do not nest: call end_undo_group, then begin the next group."
        )
        assert undo_group_server.undo_group["name"] == "Outer"
        conn.disconnect()

    @pytest.mark.asyncio
    async def test_undo_and_redo_are_refused_inside_a_group(
        self, undo_group_server, monkeypatch
    ):
        conn = self._tools(monkeypatch)
        await self._call("begin_undo_group", {"name": "Turn"})
        conn.send_command("create_object", {**self.BOX, "name": "Kept"})

        for tool in ("undo", "redo"):
            text = await self._refusal(tool, {"steps": 1})
            assert text.startswith(
                f"invalid_argument: {tool} is not available while undo group "
                "'Turn' is open\n"
            )
        await self._call("end_undo_group", {})
        assert [entry[:2] for entry in undo_group_server.undo_stack] == [("group", "Turn")]
        conn.disconnect()

    def test_end_without_an_open_group_reports_ended_false(self, undo_group_server):
        conn = self._connection()

        result = conn.send_command("end_undo_group", {})

        assert result == {"ended": False, "message": "No undo group is open."}
        conn.disconnect()

    def test_the_group_ends_when_its_client_disconnects(self, undo_group_server):
        first = self._connection()
        first.send_command("begin_undo_group", {"name": "Turn"})
        first.send_command("create_object", {**self.BOX, "name": "Orphan"})
        first.disconnect()
        deadline = time.monotonic() + 2
        while undo_group_server.undo_group and time.monotonic() < deadline:
            time.sleep(0.02)

        second = self._connection()
        result = second.send_command("end_undo_group", {})
        undone = second.send_command("undo", {"steps": 2})
        second.disconnect()

        assert result["ended"] is False
        assert result["last_group"]["name"] == "Turn"
        assert result["last_group"]["end_reason"] == "client_disconnected"
        assert result["last_group"]["command_count"] == 1
        assert undone["undone_steps"] == 1

    def test_only_the_client_that_began_a_group_can_end_it(self, undo_group_server):
        from rhinomcp.server import RhinoError

        owner, other = self._connection(), self._connection()
        owner.send_command("begin_undo_group", {"name": "Turn"})

        with pytest.raises(RhinoError) as info:
            other.send_command("end_undo_group", {})
        ended = owner.send_command("end_undo_group", {})
        owner.disconnect()
        other.disconnect()

        assert info.value.code == "invalid_argument"
        assert "was begun by another client" in info.value.message
        assert ended["ended"] is True

    @pytest.mark.parametrize("tool", ["begin_undo_group", "end_undo_group"])
    @pytest.mark.asyncio
    async def test_annotations_mark_state_change_without_destruction(self, tool):
        import rhinomcp

        listed = next(t for t in await rhinomcp.mcp.list_tools() if t.name == tool)
        assert listed.annotations.read_only_hint is False
        assert listed.annotations.destructive_hint is False
        assert listed.annotations.open_world_hint is False

    async def _call(self, tool, args):
        import rhinomcp

        return await rhinomcp.mcp.call_tool(tool, args)
