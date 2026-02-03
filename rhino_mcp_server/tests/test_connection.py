"""
Unit tests for RhinoConnection class.
Tests connection logic, JSON parsing, and error handling without requiring Rhino.
"""

import json
import pytest
import socket
from unittest.mock import Mock, patch, MagicMock


class TestRhinoConnection:
    """Tests for the RhinoConnection class."""

    def test_connection_init(self):
        """Test RhinoConnection initialization."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        assert conn.host == "127.0.0.1"
        assert conn.port == 1999
        assert conn.sock is None

    @patch('socket.socket')
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

    @patch('socket.socket')
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

    @patch('socket.socket')
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
        mock_sock.recv.return_value = json.dumps(response).encode('utf-8')

        result = conn.receive_full_response(mock_sock)

        assert json.loads(result.decode('utf-8')) == response

    def test_receive_chunked_json(self):
        """Test receiving JSON response in multiple chunks."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        response = {"status": "success", "result": {"data": "x" * 1000}}
        full_json = json.dumps(response).encode('utf-8')

        # Split into chunks
        chunk1 = full_json[:50]
        chunk2 = full_json[50:]
        mock_sock.recv.side_effect = [chunk1, chunk2]

        result = conn.receive_full_response(mock_sock)

        assert json.loads(result.decode('utf-8')) == response

    def test_receive_empty_response_raises(self):
        """Test that empty response raises exception."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        mock_sock = MagicMock()
        mock_sock.recv.return_value = b''

        with pytest.raises(Exception, match="Connection closed"):
            conn.receive_full_response(mock_sock)


class TestSendCommand:
    """Tests for the send_command method."""

    @patch('socket.socket')
    def test_send_command_success(self, mock_socket_class):
        """Test successful command sending and response parsing."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "success", "result": {"name": "Box1", "id": "abc-123"}}
        mock_sock.recv.return_value = json.dumps(response).encode('utf-8')

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        result = conn.send_command("create_object", {"type": "BOX", "params": {}})

        assert result == {"name": "Box1", "id": "abc-123"}

        # Verify the command was sent correctly
        sent_data = mock_sock.sendall.call_args[0][0]
        sent_command = json.loads(sent_data.decode('utf-8'))
        assert sent_command["type"] == "create_object"
        assert sent_command["params"]["type"] == "BOX"

    @patch('socket.socket')
    def test_send_command_error_response(self, mock_socket_class):
        """Test handling of error response from Rhino."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        response = {"status": "error", "message": "Object not found"}
        mock_sock.recv.return_value = json.dumps(response).encode('utf-8')

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        with pytest.raises(Exception, match="Object not found"):
            conn.send_command("get_object_info", {"id": "nonexistent"})

    @patch('socket.socket')
    def test_send_command_timeout(self, mock_socket_class):
        """Test handling of socket timeout."""
        from rhinomcp.server import RhinoConnection

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recv.side_effect = socket.timeout("timed out")

        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        with pytest.raises(Exception, match="Timeout"):
            conn.send_command("create_object", {"type": "BOX"})

        # Socket should be invalidated after timeout
        assert conn.sock is None

    def test_send_command_not_connected(self):
        """Test sending command when not connected."""
        from rhinomcp.server import RhinoConnection

        conn = RhinoConnection(host="127.0.0.1", port=1999)

        with pytest.raises(Exception):
            conn.send_command("test", {})


class TestEnvironmentConfig:
    """Tests for environment variable configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        import rhinomcp.server as server

        # These are the defaults when env vars are not set
        assert server.RHINO_HOST == "127.0.0.1"
        assert server.RHINO_PORT == 1999
        assert server.RHINO_TIMEOUT == 15.0

    @patch.dict('os.environ', {
        'RHINO_MCP_HOST': '192.168.1.100',
        'RHINO_MCP_PORT': '2000',
        'RHINO_MCP_TIMEOUT': '30.0'
    })
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
        os.environ.pop('RHINO_MCP_HOST', None)
        os.environ.pop('RHINO_MCP_PORT', None)
        os.environ.pop('RHINO_MCP_TIMEOUT', None)
        importlib.reload(server)
