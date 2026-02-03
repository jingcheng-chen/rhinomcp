# rhino_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
import os
import threading
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List

# Configuration from environment variables
RHINO_HOST = os.getenv("RHINO_MCP_HOST", "127.0.0.1")
RHINO_PORT = int(os.getenv("RHINO_MCP_PORT", "1999"))
RHINO_TIMEOUT = float(os.getenv("RHINO_MCP_TIMEOUT", "15.0"))
RHINO_DEBUG = os.getenv("RHINO_MCP_DEBUG", "").lower() in ("1", "true", "yes")
RHINO_LOG_LEVEL = os.getenv("RHINO_MCP_LOG_LEVEL", "DEBUG" if RHINO_DEBUG else "INFO")

# Configure logging
log_level = getattr(logging, RHINO_LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RhinoMCPServer")
logger.setLevel(log_level)

if RHINO_DEBUG:
    logger.info("Debug mode enabled")

@dataclass
class RhinoConnection:
    host: str
    port: int
    sock: socket.socket | None = None  # Changed from 'socket' to 'sock' to avoid naming conflict
    
    def connect(self) -> bool:
        """Connect to the Rhino addon socket server"""
        if self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Rhino at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Rhino: {str(e)}")
            self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from the Rhino addon"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Rhino: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks.

        Uses incremental parsing to avoid O(n^2) JSON parsing overhead.
        """
        accumulated = ""
        decoder = json.JSONDecoder()
        sock.settimeout(RHINO_TIMEOUT)

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
                            # raw_decode returns (obj, end_index) - more efficient for streaming
                            decoder.raw_decode(accumulated)
                            logger.info(f"Received complete response ({len(accumulated)} bytes)")
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
            logger.info(f"Returning data after receive completion ({len(accumulated)} bytes)")
            try:
                decoder.raw_decode(accumulated)
                return accumulated.encode('utf-8')
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Send a command to Rhino and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Rhino")
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            # Log the command being sent
            logger.info(f"Sending command: {command_type}")
            logger.debug(f"Command params: {json.dumps(params, indent=2)}")

            if self.sock is None:
                raise Exception("Socket is not connected")

            # Send the command
            command_json = json.dumps(command)
            logger.debug(f"Raw command JSON ({len(command_json)} bytes): {command_json[:500]}...")
            self.sock.sendall(command_json.encode('utf-8'))
            logger.debug("Command sent, waiting for response...")

            # Set a timeout for receiving
            self.sock.settimeout(RHINO_TIMEOUT)

            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.sock)
            logger.debug(f"Received {len(response_data)} bytes of data")

            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response status: {response.get('status', 'unknown')}")
            logger.debug(f"Full response: {json.dumps(response, indent=2)[:1000]}...")
            
            if response.get("status") == "error":
                logger.error(f"Rhino error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Rhino"))
            
            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Rhino")
            # Don't try to reconnect here - let the get_rhino_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.sock = None
            raise Exception("Timeout waiting for Rhino response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Rhino lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Rhino: {str(e)}")
            # Try to log what was received
            if 'response_data' in locals() and response_data: # type: ignore
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Rhino: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Rhino: {str(e)}")
            # Don't try to reconnect here - let the get_rhino_connection handle reconnection
            self.sock = None
            raise Exception(f"Communication error with Rhino: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools
    
    try:
        # Just log that we're starting up
        logger.info("RhinoMCP server starting up")
        
        # Try to connect to Rhino on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            rhino = get_rhino_connection()
            logger.info("Successfully connected to Rhino on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Rhino on startup: {str(e)}")
            logger.warning("Make sure the Rhino addon is running before using Rhino resources or tools")
        
        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        global _rhino_connection
        if _rhino_connection:
            logger.info("Disconnecting from Rhino on shutdown")
            _rhino_connection.disconnect()
            _rhino_connection = None
        logger.info("RhinoMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "RhinoMCP",
    lifespan=server_lifespan
)

# Resource endpoints

# Global connection for resources (since resources can't access context)
_rhino_connection = None
_connection_lock = threading.Lock()

def get_rhino_connection():
    """Get or create a persistent Rhino connection (thread-safe)"""
    global _rhino_connection

    with _connection_lock:
        # Create a new connection if needed
        if _rhino_connection is None:
            _rhino_connection = RhinoConnection(host=RHINO_HOST, port=RHINO_PORT)
            if not _rhino_connection.connect():
                logger.error("Failed to connect to Rhino")
                _rhino_connection = None
                raise Exception("Could not connect to Rhino. Make sure the Rhino addon is running.")
            logger.info("Created new persistent connection to Rhino")

        return _rhino_connection

# Main execution
def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()