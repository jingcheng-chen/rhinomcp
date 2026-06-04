"""
Unit tests for RhinoConnection class.
Tests connection logic, JSON parsing, and error handling without requiring Rhino.
"""

import json
import pytest
import socket
from unittest.mock import patch, MagicMock


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
        """Test receiving a complete JSON response in one chunk."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        response = {"status": "success", "result": {"id": "123"}}
        mock_sock.recv.return_value = json.dumps(response).encode("utf-8")

        result = conn.receive_full_response(mock_sock)

        assert json.loads(result.decode("utf-8")) == response

    def test_receive_chunked_json(self):
        """Test receiving JSON response in multiple chunks."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        response = {"status": "success", "result": {"data": "x" * 1000}}
        full_json = json.dumps(response).encode("utf-8")

        # Split into chunks
        chunk1 = full_json[:50]
        chunk2 = full_json[50:]
        mock_sock.recv.side_effect = [chunk1, chunk2]

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
        mock_sock.recv.return_value = json.dumps(
            {"status": "success", "result": {}}
        ).encode("utf-8")

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


class TestSendCommand:
    """Tests for the send_command method."""

    @patch("socket.socket")
    def test_send_command_success(self, mock_socket_class):
        """Test successful command sending and response parsing."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "success", "result": {"name": "Box1", "id": "abc-123"}}
        mock_sock.recv.return_value = json.dumps(response).encode("utf-8")

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        result = conn.send_command(
            "create_object",
            {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}},
        )

        assert result == {"name": "Box1", "id": "abc-123"}

        # Verify the command was sent correctly
        sent_data = mock_sock.sendall.call_args[0][0]
        sent_command = json.loads(sent_data.decode("utf-8"))
        assert sent_command["type"] == "create_object"
        assert sent_command["params"]["type"] == "BOX"

    @patch("socket.socket")
    def test_send_command_error_response(self, mock_socket_class):
        """Test handling of error response from Rhino."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "error", "message": "Object not found"}
        mock_sock.recv.return_value = json.dumps(response).encode("utf-8")

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

        # Socket timeout leads to "No data received" which is wrapped as communication error
        with pytest.raises(Exception, match="Communication error with Rhino"):
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
