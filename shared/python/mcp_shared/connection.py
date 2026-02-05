"""
Base connection class for MCP plugin communication.

Provides a reusable TCP socket connection with JSON protocol support.
"""

import json
import logging
import os
import socket
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='PluginConnection')


@dataclass
class PluginConnection:
    """
    Base class for TCP connections to Rhino/Grasshopper plugins.

    Handles socket management, JSON protocol, and chunked response handling.
    Subclasses can override for plugin-specific behavior if needed.
    """
    host: str
    port: int
    timeout: float = 15.0
    sock: socket.socket | None = field(default=None, repr=False)

    def connect(self) -> bool:
        """Connect to the plugin socket server."""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to plugin at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to plugin: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the plugin."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """
        Receive the complete JSON response, potentially in multiple chunks.

        Uses incremental parsing to detect complete JSON without O(n^2) overhead.
        """
        accumulated = ""
        decoder = json.JSONDecoder()
        sock.settimeout(self.timeout)

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not accumulated:
                            raise Exception("Connection closed before receiving any data")
                        break

                    accumulated += chunk.decode('utf-8')

                    # Only attempt parsing when we see a closing brace (optimization)
                    if accumulated.rstrip().endswith('}'):
                        try:
                            # raw_decode returns (obj, end_index) - efficient for streaming
                            decoder.raw_decode(accumulated)
                            logger.debug(f"Received complete response ({len(accumulated)} bytes)")
                            return accumulated.encode('utf-8')
                        except json.JSONDecodeError:
                            # Incomplete JSON, continue receiving
                            continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

        # Try to use what we have
        if accumulated:
            logger.debug(f"Returning data after receive completion ({len(accumulated)} bytes)")
            try:
                decoder.raw_decode(accumulated)
                return accumulated.encode('utf-8')
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Send a command to the plugin and return the response.

        Args:
            command_type: The type of command to execute
            params: Command parameters as a dictionary

        Returns:
            The result from the command execution

        Raises:
            ConnectionError: If not connected
            Exception: On communication errors
        """
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to plugin")

        command = {
            "type": command_type,
            "params": params or {}
        }

        try:
            logger.info(f"Sending command: {command_type}")
            logger.debug(f"Command params: {json.dumps(params, indent=2)}")

            if self.sock is None:
                raise Exception("Socket is not connected")

            # Send the command
            command_json = json.dumps(command)
            self.sock.sendall(command_json.encode('utf-8'))

            # Set timeout and receive response
            self.sock.settimeout(self.timeout)
            response_data = self.receive_full_response(self.sock)

            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Plugin error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from plugin"))

            return response.get("result", {})

        except socket.timeout:
            logger.error("Socket timeout while waiting for response")
            self.sock = None
            raise Exception("Timeout waiting for plugin response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to plugin lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise Exception(f"Invalid response from plugin: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with plugin: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with plugin: {str(e)}")


def create_connection_manager(
    connection_class: Type[T],
    host_env: str,
    port_env: str,
    timeout_env: str,
    default_host: str = "127.0.0.1",
    default_port: int = 1999,
    default_timeout: float = 15.0,
    logger: Optional[logging.Logger] = None
) -> tuple[Callable[[], T], Callable[[], None]]:
    """
    Factory to create a thread-safe connection manager.

    Args:
        connection_class: The connection class to instantiate
        host_env: Environment variable name for host
        port_env: Environment variable name for port
        timeout_env: Environment variable name for timeout
        default_host: Default host if env var not set
        default_port: Default port if env var not set
        default_timeout: Default timeout if env var not set
        logger: Optional logger instance

    Returns:
        Tuple of (get_connection, cleanup_connection) functions
    """
    _connection: Optional[T] = None
    _lock = threading.Lock()
    _logger = logger or logging.getLogger(__name__)

    def get_connection() -> T:
        nonlocal _connection
        with _lock:
            if _connection is None:
                host = os.getenv(host_env, default_host)
                port = int(os.getenv(port_env, str(default_port)))
                timeout = float(os.getenv(timeout_env, str(default_timeout)))

                _connection = connection_class(host=host, port=port, timeout=timeout)
                if not _connection.connect():
                    _logger.error("Failed to connect to plugin")
                    _connection = None
                    raise Exception("Could not connect to plugin. Make sure it's running.")
                _logger.info("Created new persistent connection to plugin")
            return _connection

    def cleanup_connection() -> None:
        nonlocal _connection
        with _lock:
            if _connection:
                _logger.info("Disconnecting from plugin")
                _connection.disconnect()
                _connection = None

    return get_connection, cleanup_connection
