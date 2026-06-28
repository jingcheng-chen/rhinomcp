"""
Unit tests for RhinoConnection class.
Tests connection logic, JSON parsing, and error handling without requiring Rhino.
"""

import json
import pytest
import socket
from unittest.mock import patch, MagicMock


def frame(payload: bytes) -> bytes:
    """Wrap a payload in the wire protocol's 4-byte big-endian length header."""
    return len(payload).to_bytes(4, "big") + payload


def buffered_recv(wire_bytes: bytes):
    """A recv side_effect that serves wire_bytes honoring the requested byte
    count, like a real socket buffer. Returns b"" once drained (peer close)."""
    buffer = bytearray(wire_bytes)

    def recv(n):
        chunk = bytes(buffer[:n])
        del buffer[:n]
        return chunk

    return recv


class TestRhinoConnection:
    """Tests for the RhinoConnection class."""

    def test_connection_init(self):
        """Test RhinoConnection initialization."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        assert conn.host == "127.0.0.1"
        assert conn.port == 1999
        assert conn.sock is None

    @patch("socket.socket")
    def test_connect_success(self, mock_socket_class):
        """Test successful connection."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        result = conn.connect()

        assert result is True
        assert conn.sock is not None
        mock_sock.connect.assert_called_once_with(("127.0.0.1", 1999))

    @patch("socket.socket")
    def test_connect_failure(self, mock_socket_class):
        """Test connection failure handling."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        result = conn.connect()

        assert result is False
        assert conn.sock is None

    @patch("socket.socket")
    def test_disconnect(self, mock_socket_class):
        """Test disconnection."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()
        conn.disconnect()

        mock_sock.close.assert_called_once()
        assert conn.sock is None

    def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected doesn't raise."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        # Should not raise
        conn.disconnect()
        assert conn.sock is None


class TestReceiveFullResponse:
    """Tests for the receive_full_response method."""

    def test_receive_complete_json(self):
        """Test receiving a complete framed response."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        response = {"status": "success", "result": {"id": "123"}}
        wire = frame(json.dumps(response).encode("utf-8"))
        mock_sock.recv.side_effect = buffered_recv(wire)

        result = conn.receive_full_response(mock_sock)

        assert json.loads(result.decode("utf-8")) == response

    def test_receive_chunked_json(self):
        """Test receiving a frame split across multiple TCP segments."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        response = {"status": "success", "result": {"data": "x" * 1000}}
        wire = frame(json.dumps(response).encode("utf-8"))

        # Header alone, then the body dribbling in: sockets may return fewer
        # bytes than requested.
        chunks = [wire[:4], wire[4:54], wire[54:]]
        mock_sock.recv.side_effect = chunks

        result = conn.receive_full_response(mock_sock)

        assert json.loads(result.decode("utf-8")) == response

    def test_receive_empty_response_raises(self):
        """Test that empty response raises exception."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""

        with pytest.raises(Exception, match="Connection closed"):
            conn.receive_full_response(mock_sock)


class TestWireFraming:
    """Length-prefixed framing: message boundaries are read, not guessed."""

    def test_consecutive_responses_do_not_bleed(self):
        """Two responses back-to-back in the receive buffer is legal TCP.
        The old endswith-'}' + raw_decode heuristic passed both to one
        json.loads, which raised 'Extra data' and lost the second response.
        Framed reads return exactly one message per call."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        resp1 = json.dumps({"status": "success", "result": {"sequence": 1}})
        resp2 = json.dumps({"status": "success", "result": {"sequence": 2}})
        wire = frame(resp1.encode("utf-8")) + frame(resp2.encode("utf-8"))

        mock_sock = MagicMock()
        mock_sock.recv.side_effect = buffered_recv(wire)

        first = conn.receive_full_response(mock_sock)
        second = conn.receive_full_response(mock_sock)

        assert json.loads(first)["result"]["sequence"] == 1
        assert json.loads(second)["result"]["sequence"] == 2

    def test_unframed_response_raises_actionable_error(self):
        """An old plugin replies with bare JSON where the header should be.
        That must fail with update guidance, not a bogus 2 GB frame length."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        bare = json.dumps({"status": "success", "result": {}}).encode("utf-8")
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = buffered_recv(bare)

        with pytest.raises(Exception, match="predates length-prefixed framing"):
            conn.receive_full_response(mock_sock)

    def test_oversized_frame_rejected(self):
        from rhinomcp.server import MAX_FRAME_SIZE, RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        header = (MAX_FRAME_SIZE + 1).to_bytes(4, "big")
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = buffered_recv(header)

        with pytest.raises(Exception, match="Invalid response frame length"):
            conn.receive_full_response(mock_sock)

    def test_connection_closed_mid_frame_raises(self):
        """EOF after the header but before the body completes must surface as
        a connection error, not hang or return a truncated message."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        body = json.dumps({"status": "success", "result": {}}).encode("utf-8")
        wire = frame(body)[: 4 + len(body) // 2]  # header + half the body
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = buffered_recv(wire)

        with pytest.raises(ConnectionError, match="mid-message"):
            conn.receive_full_response(mock_sock)


class TestRemoteBindingGate:
    """Non-loopback hosts require an explicit RHINO_MCP_ALLOW_REMOTE opt-in,
    otherwise importing the server module raises."""

    @patch.dict("os.environ", {"RHINO_MCP_HOST": "10.0.0.5"}, clear=False)
    def test_remote_host_refused_without_opt_in(self):
        # Run cleanly whether or not rhinomcp.server is already imported:
        # we wipe it from sys.modules so the patched env always takes effect.
        import importlib
        import sys

        sys.modules.pop("rhinomcp.server", None)
        with pytest.raises(RuntimeError, match="non-loopback"):
            importlib.import_module("rhinomcp.server")
        # Restore default state so later tests don't inherit the broken module.
        import os

        os.environ.pop("RHINO_MCP_HOST", None)
        sys.modules.pop("rhinomcp.server", None)
        importlib.import_module("rhinomcp.server")


class TestConcurrencySafety:
    """The persistent socket is shared. send_command must serialize so
    interleaved write/read pairs don't attach the wrong response to the
    wrong request."""

    def test_send_command_holds_a_lock(self):
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        # _send_lock exists and is a re-entrant-safe Lock.
        assert hasattr(conn, "_send_lock")
        # Round-trip the lock to confirm it acts like threading.Lock.
        assert conn._send_lock.acquire(blocking=False)
        assert not conn._send_lock.acquire(blocking=False)
        conn._send_lock.release()


class TestRuntimeValidation:
    """Pre-flight schema validation modes."""

    @patch("socket.socket")
    def test_strict_mode_rejects_invalid_payload(self, mock_socket_class):
        import rhinomcp.server as srv
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            with pytest.raises(ValueError, match="Invalid params"):
                conn.send_command(
                    "create_object", {"type": "BOX", "params": {"radius": 1}}
                )
        finally:
            srv.RHINO_VALIDATE = original_mode

        mock_sock.sendall.assert_not_called()

    @patch("socket.socket")
    def test_warn_mode_lets_invalid_payload_through(self, mock_socket_class):
        """The default 'warn' mode logs but still sends — important while
        wrappers and schemas are still converging."""
        import rhinomcp.server as srv
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recv.side_effect = buffered_recv(
            frame(json.dumps({"status": "success", "result": {}}).encode("utf-8"))
        )

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "warn"
        try:
            conn.send_command("create_object", {"type": "BOX", "params": {"radius": 1}})
        finally:
            srv.RHINO_VALIDATE = original_mode

        mock_sock.sendall.assert_called_once()

    def test_unrecognized_validate_value_falls_back_to_warn(self):
        """Unknown RHINO_MCP_VALIDATE values must not NameError during import:
        the warning is deferred until after `logger` is constructed."""
        import importlib
        import sys

        sys.modules.pop("rhinomcp.server", None)
        with patch.dict("os.environ", {"RHINO_MCP_VALIDATE": "verbose"}, clear=False):
            try:
                mod = importlib.import_module("rhinomcp.server")
                assert mod.RHINO_VALIDATE == "warn"
            finally:
                sys.modules.pop("rhinomcp.server", None)
        # Restore baseline module so later tests see a clean import.
        importlib.import_module("rhinomcp.server")


class TestResponseValidation:
    """Post-flight schema validation of Rhino responses, behind the same
    RHINO_MCP_VALIDATE switch as the pre-flight check."""

    # A create_object result that satisfies responses/object_info.json.
    VALID_OBJECT_INFO = {
        "id": "12345678-1234-1234-1234-123456789012",
        "name": "MyBox",
        "type": "BOX",
        "layer": "Default",
        "material": "-1",
        "color": {"r": 255, "g": 0, "b": 0},
        "bounding_box": [[-1, -1, -1], [1, 1, 1]],
        "geometry": {},
    }

    # Valid params so the pre-flight check passes and the response check is
    # the only thing under test.
    VALID_BOX_PARAMS = {
        "type": "BOX",
        "params": {"width": 1.0, "length": 1.0, "height": 1.0},
    }

    def _connect_with_response(self, mock_socket_class, result):
        """Connection whose next receive yields the given result payload.

        Stubs receive_full_response rather than raw socket bytes: these tests
        pin validation policy, not wire framing, so they stay valid if the
        wire format changes (framing has its own coverage).
        """
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()
        payload = json.dumps({"status": "success", "result": result}).encode(
            "utf-8"
        )
        conn.receive_full_response = lambda sock, buffer_size=8192: payload
        return conn

    @patch("socket.socket")
    def test_strict_mode_rejects_contract_violating_response(
        self, mock_socket_class
    ):
        import rhinomcp.server as srv

        # An empty result is missing every required object_info field.
        conn = self._connect_with_response(mock_socket_class, {})

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            with pytest.raises(ValueError, match="failed contract validation"):
                conn.send_command("create_object", self.VALID_BOX_PARAMS)
        finally:
            srv.RHINO_VALIDATE = original_mode

    @patch("socket.socket")
    def test_strict_mode_passes_valid_response_through(self, mock_socket_class):
        import rhinomcp.server as srv

        conn = self._connect_with_response(
            mock_socket_class, self.VALID_OBJECT_INFO
        )

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            result = conn.send_command("create_object", self.VALID_BOX_PARAMS)
        finally:
            srv.RHINO_VALIDATE = original_mode

        assert result == self.VALID_OBJECT_INFO

    @patch("socket.socket")
    def test_warn_mode_logs_and_returns_result_anyway(
        self, mock_socket_class, caplog
    ):
        """The default 'warn' mode must never turn a successful Rhino command
        into a client error — the command already executed."""
        import rhinomcp.server as srv

        conn = self._connect_with_response(mock_socket_class, {})

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "warn"
        try:
            with caplog.at_level("WARNING", logger="RhinoMCPServer"):
                result = conn.send_command("create_object", self.VALID_BOX_PARAMS)
        finally:
            srv.RHINO_VALIDATE = original_mode

        assert result == {}
        assert any(
            "Response validation failed for create_object" in r.message
            for r in caplog.records
        )

    @patch("socket.socket")
    def test_unmapped_command_skips_response_validation(self, mock_socket_class):
        """get_selected_objects_info returns {"selected_objects": [...]}, which
        no response schema describes — it must pass untouched even in strict."""
        import rhinomcp.server as srv

        result_payload = {"selected_objects": [{"id": "1", "name": "Box1"}]}
        conn = self._connect_with_response(mock_socket_class, result_payload)

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            result = conn.send_command("get_selected_objects_info", {})
        finally:
            srv.RHINO_VALIDATE = original_mode

        assert result == result_payload

    @patch("socket.socket")
    def test_schema_infrastructure_error_never_fails_the_command(
        self, mock_socket_class, caplog
    ):
        """A broken schema (unresolvable $ref, unreadable file) is not a
        verdict on the response. Even in strict mode the result must come
        back, with a 'could not validate' warning instead of a failure."""
        import rhinomcp.server as srv

        conn = self._connect_with_response(
            mock_socket_class, self.VALID_OBJECT_INFO
        )

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            with patch(
                "rhinomcp.validation.validate_response",
                side_effect=RuntimeError("Unresolvable: object_info.json"),
            ):
                with caplog.at_level("WARNING", logger="RhinoMCPServer"):
                    result = conn.send_command(
                        "create_object", self.VALID_BOX_PARAMS
                    )
        finally:
            srv.RHINO_VALIDATE = original_mode

        assert result == self.VALID_OBJECT_INFO
        assert any(
            "Could not validate response for create_object" in r.message
            for r in caplog.records
        )

    # A result that satisfies the closed responses/object_attributes.json
    # (additionalProperties:false), used to prove perception keys are stripped
    # before validation rather than rejected by it.
    VALID_OBJECT_ATTRIBUTES = {
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
        "color_source": "by_layer",
        "material_index": -1,
        "material_source": "by_layer",
        "visible": True,
        "locked": False,
        "hidden": False,
        "normal": True,
        "user_strings": {},
    }

    @patch("socket.socket")
    def test_perception_keys_do_not_fail_closed_schema(self, mock_socket_class):
        """With perception on, the plugin injects _delta/_health into a mutating
        command's result. object_attributes.json is closed, so validating the
        raw result would reject those keys and turn a successful
        update_object_attributes into a strict-mode error. They must be stripped
        before validation, and still come back to the caller."""
        import rhinomcp.server as srv

        result_with_perception = {
            **self.VALID_OBJECT_ATTRIBUTES,
            "_delta": {
                "created_ids": [],
                "deleted_ids": [],
                "count_before": 1,
                "count_after": 1,
            },
            "_health": {
                "checked_count": 0,
                "invalid_count": 0,
                "issues": [],
                "truncated": False,
            },
        }
        conn = self._connect_with_response(
            mock_socket_class, result_with_perception
        )

        original_mode = srv.RHINO_VALIDATE
        srv.RHINO_VALIDATE = "strict"
        try:
            result = conn.send_command(
                "update_object_attributes",
                {"id": "12345678-1234-1234-1234-123456789012", "visible": True},
            )
        finally:
            srv.RHINO_VALIDATE = original_mode

        # No raise in strict mode, and the perception blocks survive untouched
        # in the returned result.
        assert result["name"] == "MyBox"
        assert result["_delta"]["count_after"] == 1
        assert result["_health"]["invalid_count"] == 0


class TestPerceptionForwarding:
    """Opt-in perception forwards an envelope-level include_delta flag and
    passes the plugin's _delta block straight through to the caller."""

    def _connect(self, mock_socket_class, result):
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        # Responses are length-prefixed on the wire (framing), so frame the
        # canned response the way the plugin would.
        mock_sock.recv.side_effect = buffered_recv(
            frame(json.dumps({"status": "success", "result": result}).encode("utf-8"))
        )
        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()
        return conn, mock_sock

    @patch("socket.socket")
    def test_off_by_default_no_flag_sent(self, mock_socket_class):
        import rhinomcp.server as srv

        conn, mock_sock = self._connect(mock_socket_class, {})
        original = srv.RHINO_PERCEPTION
        srv.RHINO_PERCEPTION = False
        try:
            conn.send_command("create_object", {"type": "BOX", "params": {}})
        finally:
            srv.RHINO_PERCEPTION = original

        sent = json.loads(mock_sock.sendall.call_args[0][0][4:].decode("utf-8"))  # skip frame header
        assert "include_delta" not in sent  # byte-identical to pre-feature

    @patch("socket.socket")
    def test_on_sends_envelope_flag_without_touching_params(self, mock_socket_class):
        import rhinomcp.server as srv

        conn, mock_sock = self._connect(mock_socket_class, {})
        original = srv.RHINO_PERCEPTION
        srv.RHINO_PERCEPTION = True
        try:
            conn.send_command("create_object", {"type": "BOX", "params": {"width": 1}})
        finally:
            srv.RHINO_PERCEPTION = original

        sent = json.loads(mock_sock.sendall.call_args[0][0][4:].decode("utf-8"))  # skip frame header
        # Flag rides on the envelope, never inside params (so it can't trip
        # params schema validation or collide with a real parameter).
        assert sent["include_delta"] is True
        assert "include_delta" not in sent["params"]
        assert sent["params"] == {"type": "BOX", "params": {"width": 1}}

    @patch("socket.socket")
    def test_delta_in_result_flows_through(self, mock_socket_class):
        import rhinomcp.server as srv

        delta = {
            "created_count": 1,
            "deleted_count": 0,
            "count_before": 0,
            "count_after": 1,
            "created_ids": ["11111111-1111-1111-1111-111111111111"],
            "deleted_ids": [],
            "truncated": False,
        }
        conn, _ = self._connect(mock_socket_class, {"id": "x", "_delta": delta})
        original = srv.RHINO_PERCEPTION
        srv.RHINO_PERCEPTION = True
        try:
            result = conn.send_command("create_object", {"type": "BOX", "params": {}})
        finally:
            srv.RHINO_PERCEPTION = original

        assert result["_delta"] == delta


class TestSendCommand:
    """Tests for the send_command method."""

    @patch("socket.socket")
    def test_send_command_success(self, mock_socket_class):
        """Test successful command sending and response parsing."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "success", "result": {"name": "Box1", "id": "abc-123"}}
        mock_sock.recv.side_effect = buffered_recv(
            frame(json.dumps(response).encode("utf-8"))
        )

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        result = conn.send_command(
            "create_object",
            {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}},
        )

        assert result == {"name": "Box1", "id": "abc-123"}

        # Verify the command went out as one frame: 4-byte big-endian length
        # header followed by the JSON payload.
        sent_data = mock_sock.sendall.call_args[0][0]
        assert int.from_bytes(sent_data[:4], "big") == len(sent_data) - 4
        sent_command = json.loads(sent_data[4:].decode("utf-8"))
        assert sent_command["type"] == "create_object"
        assert sent_command["params"]["type"] == "BOX"

    @patch("socket.socket")
    def test_send_command_error_response(self, mock_socket_class):
        """Test handling of error response from Rhino."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "error", "message": "Object not found"}
        mock_sock.recv.side_effect = buffered_recv(
            frame(json.dumps(response).encode("utf-8"))
        )

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        with pytest.raises(Exception, match="Object not found"):
            conn.send_command(
                "get_object_info",
                {"id": "00000000-0000-0000-0000-000000000000"},
            )

    @patch("socket.socket")
    def test_send_command_timeout(self, mock_socket_class):
        """Test handling of socket timeout."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recv.side_effect = socket.timeout("timed out")

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        # Receive timeouts propagate to the dedicated timeout handler
        with pytest.raises(Exception, match="Timeout waiting for Rhino response"):
            conn.send_command(
                "create_object",
                {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}},
            )

        # Socket should be invalidated after timeout
        assert conn.sock is None

    @patch("socket.socket")
    def test_send_command_not_connected(self, mock_socket_class):
        """Test sending command when not connected."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        with pytest.raises(Exception, match="mcpstart") as exc:
            conn.send_command("test", {})

        assert "Please start Rhino" in str(exc.value)
        assert "127.0.0.1:1999" in str(exc.value)

    @patch("time.sleep", return_value=None)
    @patch("socket.socket")
    def test_readonly_command_retries_transient_connection_drop(
        self, mock_socket_class, _mock_sleep
    ):
        """Read-only discovery commands can safely retry a dropped socket once."""
        from rhinomcp.server import RhinoConnection

        first_sock = MagicMock()
        first_sock.recv.return_value = b""
        second_sock = MagicMock()
        second_sock.recv.side_effect = buffered_recv(
            frame(
                json.dumps(
                    {"status": "success", "result": {"found_count": 1}}
                ).encode("utf-8")
            )
        )
        mock_socket_class.side_effect = [first_sock, second_sock]

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        result = conn.send_command(
            "gh_batch_search_components", {"queries": ["Square"]}
        )

        assert result == {"found_count": 1}
        assert mock_socket_class.call_count == 2
        first_sock.sendall.assert_called_once()
        second_sock.sendall.assert_called_once()

    @patch("socket.socket")
    def test_mutating_command_does_not_retry_transient_connection_drop(
        self, mock_socket_class
    ):
        """Mutating commands are not retried because the first attempt may have side effects."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        mock_socket_class.return_value = mock_sock

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        with pytest.raises(Exception, match="interrupted"):
            conn.send_command(
                "create_object",
                {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}},
            )

        assert mock_socket_class.call_count == 1
        mock_sock.sendall.assert_called_once()
        assert conn.sock is None

    @patch("socket.socket")
    def test_get_rhino_connection_failure_shows_mcpstart_guidance(
        self, mock_socket_class
    ):
        """Global connection creation should tell callers how to start RhinoMCP."""
        import rhinomcp.server as server

        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_sock

        original_connection = server._rhino_connection
        server._rhino_connection = None
        try:
            with pytest.raises(Exception, match="mcpstart") as exc:
                server.get_rhino_connection()
        finally:
            server._rhino_connection = original_connection

        assert "Please start Rhino" in str(exc.value)
        assert "127.0.0.1:1999" in str(exc.value)


class TestEnvironmentConfig:
    """Tests for environment variable configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        import rhinomcp.server as server

        # These are the defaults when env vars are not set
        assert server.RHINO_HOST == "127.0.0.1"
        assert server.RHINO_PORT == 1999
        assert server.RHINO_TIMEOUT == 15.0

    @patch.dict(
        "os.environ",
        {
            "RHINO_MCP_HOST": "192.168.1.100",
            "RHINO_MCP_PORT": "2000",
            "RHINO_MCP_TIMEOUT": "30.0",
            # The non-loopback safety check kicks in here; tell it we know.
            "RHINO_MCP_ALLOW_REMOTE": "1",
        },
    )
    def test_custom_config(self):
        """Test custom configuration from environment variables."""
        # Need to reload the module to pick up new env vars
        import importlib
        import rhinomcp.server as server

        importlib.reload(server)

        assert server.RHINO_HOST == "192.168.1.100"
        assert server.RHINO_PORT == 2000
        assert server.RHINO_TIMEOUT == 30.0

        # Reload again to restore defaults for other tests
        import os

        os.environ.pop("RHINO_MCP_HOST", None)
        os.environ.pop("RHINO_MCP_PORT", None)
        os.environ.pop("RHINO_MCP_TIMEOUT", None)
        importlib.reload(server)
