"""Grasshopper MCP Server - Main server configuration."""

import logging
import os
import socket
import json
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict

from mcp.server.fastmcp import FastMCP

# Configuration from environment variables
GH_HOST = os.getenv("GRASSHOPPER_MCP_HOST", "127.0.0.1")
GH_PORT = int(os.getenv("GRASSHOPPER_MCP_PORT", "2000"))
GH_TIMEOUT = float(os.getenv("GRASSHOPPER_MCP_TIMEOUT", "15.0"))
GH_DEBUG = os.getenv("GRASSHOPPER_MCP_DEBUG", "").lower() in ("1", "true", "yes")
GH_LOG_LEVEL = os.getenv("GRASSHOPPER_MCP_LOG_LEVEL", "DEBUG" if GH_DEBUG else "INFO")

# Configure logging
log_level = getattr(logging, GH_LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GrasshopperMCPServer")
logger.setLevel(log_level)


@dataclass
class GrasshopperConnection:
    """Connection to the Grasshopper MCP plugin via TCP socket."""
    host: str
    port: int
    timeout: float = 15.0
    sock: socket.socket | None = field(default=None, repr=False)

    def connect(self) -> bool:
        """Connect to the Grasshopper plugin socket server."""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Grasshopper at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Grasshopper: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the Grasshopper plugin."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Grasshopper: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """Receive the complete response, potentially in multiple chunks."""
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

                    if accumulated.rstrip().endswith('}'):
                        try:
                            decoder.raw_decode(accumulated)
                            logger.debug(f"Received complete response ({len(accumulated)} bytes)")
                            return accumulated.encode('utf-8')
                        except json.JSONDecodeError:
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

        if accumulated:
            try:
                decoder.raw_decode(accumulated)
                return accumulated.encode('utf-8')
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Send a command to Grasshopper and return the response."""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Grasshopper")

        command = {
            "type": command_type,
            "params": params or {}
        }

        try:
            logger.info(f"Sending command: {command_type}")
            logger.debug(f"Command params: {json.dumps(params, indent=2)}")

            if self.sock is None:
                raise Exception("Socket is not connected")

            command_json = json.dumps(command)
            self.sock.sendall(command_json.encode('utf-8'))

            self.sock.settimeout(self.timeout)
            response_data = self.receive_full_response(self.sock)

            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Grasshopper error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Grasshopper"))

            return response.get("result", {})

        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Grasshopper")
            self.sock = None
            raise Exception("Timeout waiting for Grasshopper response")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Grasshopper lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Grasshopper: {str(e)}")
            raise Exception(f"Invalid response from Grasshopper: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Grasshopper: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Grasshopper: {str(e)}")


# Global connection management
_gh_connection: GrasshopperConnection | None = None
_connection_lock = threading.Lock()


def get_grasshopper_connection() -> GrasshopperConnection:
    """Get or create a persistent Grasshopper connection (thread-safe)."""
    global _gh_connection

    with _connection_lock:
        if _gh_connection is None:
            _gh_connection = GrasshopperConnection(host=GH_HOST, port=GH_PORT, timeout=GH_TIMEOUT)
            if not _gh_connection.connect():
                logger.error("Failed to connect to Grasshopper")
                _gh_connection = None
                raise Exception("Could not connect to Grasshopper. Make sure the GH plugin is running (GHMCPStart command).")
            logger.info("Created new persistent connection to Grasshopper")

        return _gh_connection


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle."""
    try:
        logger.info("GrasshopperMCP server starting up")

        try:
            gh = get_grasshopper_connection()
            logger.info("Successfully connected to Grasshopper on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Grasshopper on startup: {str(e)}")
            logger.warning("Make sure the Grasshopper plugin is running before using tools")

        yield {}
    finally:
        global _gh_connection
        if _gh_connection:
            logger.info("Disconnecting from Grasshopper on shutdown")
            _gh_connection.disconnect()
            _gh_connection = None
        logger.info("GrasshopperMCP server shut down")


# Create the MCP server
mcp = FastMCP(
    "GrasshopperMCP",
    lifespan=server_lifespan
)
