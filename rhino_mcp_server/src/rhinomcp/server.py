# rhino_mcp_server.py
from mcp.server.fastmcp import FastMCP
import socket
import json
import logging
import os
import threading
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

# Configuration from environment variables
RHINO_HOST = os.getenv("RHINO_MCP_HOST", "127.0.0.1")
RHINO_PORT = int(os.getenv("RHINO_MCP_PORT", "1999"))
# Sending arbitrary tool payloads (including run_command / execute_rhinoscript)
# over a non-loopback link with no authentication is genuinely dangerous.
# Refuse non-loopback connect targets unless the operator opts in explicitly.
RHINO_ALLOW_REMOTE = os.getenv("RHINO_MCP_ALLOW_REMOTE", "").lower() in ("1", "true", "yes")
if RHINO_HOST not in ("127.0.0.1", "::1", "localhost") and not RHINO_ALLOW_REMOTE:
    raise RuntimeError(
        f"RHINO_MCP_HOST={RHINO_HOST!r} is non-loopback. The TCP bridge to Rhino "
        "carries unauthenticated commands including arbitrary-code execution; "
        "set RHINO_MCP_ALLOW_REMOTE=1 to acknowledge the risk and proceed."
    )
RHINO_TIMEOUT = float(os.getenv("RHINO_MCP_TIMEOUT", "15.0"))
RHINO_DEBUG = os.getenv("RHINO_MCP_DEBUG", "").lower() in ("1", "true", "yes")
RHINO_LOG_LEVEL = os.getenv("RHINO_MCP_LOG_LEVEL", "DEBUG" if RHINO_DEBUG else "INFO")
# Pre-flight schema validation. Three modes:
#   "off"    - skip entirely
#   "warn"   - log violations but still send (default; safe while wrappers/schemas
#              converge)
#   "strict" - raise ValueError before the socket send (recommended in CI)
RHINO_VALIDATE = os.getenv("RHINO_MCP_VALIDATE", "warn").lower()
if RHINO_VALIDATE in ("0", "false", "no"):
    RHINO_VALIDATE = "off"
elif RHINO_VALIDATE in ("1", "true", "yes"):
    RHINO_VALIDATE = "warn"
if RHINO_VALIDATE not in ("off", "warn", "strict"):
    logger.warning(f"Unknown RHINO_MCP_VALIDATE={RHINO_VALIDATE!r}; falling back to 'warn'.")
    RHINO_VALIDATE = "warn"

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

    def __post_init__(self):
        # Serializes the request/response cycle on the persistent socket.
        # Without this, two MCP tool calls landing on different threads can
        # interleave their write/read pairs and the wrong response gets attached
        # to the wrong request.
        self._send_lock = threading.Lock()

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
        """Send a command to Rhino and return the response. Thread-safe: serialized
        across concurrent callers so request/response framing isn't interleaved."""
        with self._send_lock:
            return self._send_command_locked(command_type, params)

    def _send_command_locked(self, command_type: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
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

            # Pre-flight: validate against the JSON Schema contract before touching
            # the socket. In 'warn' mode we log and continue (safe default); in
            # 'strict' we raise so the bad payload never reaches Rhino.
            # validate_command no-ops if jsonschema is missing or the command has
            # no schema yet.
            if RHINO_VALIDATE != "off":
                from rhinomcp.validation import validate_command
                try:
                    validate_command(command_type, command["params"], raise_on_error=True)
                except ValueError:
                    raise
                except Exception as ve:
                    msg = f"Pre-flight validation failed for {command_type}: {ve}"
                    if RHINO_VALIDATE == "strict":
                        raise ValueError(f"Invalid params for '{command_type}': {ve}") from ve
                    logger.warning(msg)

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
        except ValueError:
            # Pre-flight validation failures — local, not a transport issue. Propagate.
            raise
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


# ============================================================================
# MCP Resources - Browsable RhinoScript Documentation
# ============================================================================

# Import rhinoscriptsyntax_json for resources
from rhinomcp.static.rhinoscriptsyntax import rhinoscriptsyntax_json


@mcp.resource("rhinoscript://modules")
def resource_list_modules() -> str:
    """
    List all RhinoScript modules with function counts.
    Browse this to discover what's available.
    """
    lines = ["# RhinoScript Modules\n"]
    lines.append("| Module | Functions |")
    lines.append("|--------|-----------|")

    for module in sorted(rhinoscriptsyntax_json, key=lambda m: m["ModuleName"]):
        name = module["ModuleName"]
        count = len(module["functions"])
        lines.append(f"| {name} | {count} |")

    lines.append("\n\nUse `rhinoscript://module/<name>` to browse a specific module.")
    return "\n".join(lines)


@mcp.resource("rhinoscript://module/{module_name}")
def resource_get_module(module_name: str) -> str:
    """
    Get all functions in a specific module with signatures.
    """
    for module in rhinoscriptsyntax_json:
        if module["ModuleName"].lower() == module_name.lower():
            lines = [f"# RhinoScript Module: {module['ModuleName']}\n"]
            lines.append(f"Total functions: {len(module['functions'])}\n")

            for func in module["functions"]:
                sig = func.get("Signature", func["Name"] + "()")
                desc = func.get("Description", "")[:100]
                lines.append(f"## {func['Name']}")
                lines.append(f"```python\nrs.{sig}\n```")
                lines.append(f"{desc}\n")

            return "\n".join(lines)

    available = ", ".join(sorted(m["ModuleName"] for m in rhinoscriptsyntax_json))
    return f"Module '{module_name}' not found.\n\nAvailable modules: {available}"


@mcp.resource("rhinoscript://function/{function_name}")
def resource_get_function(function_name: str) -> str:
    """
    Get complete documentation for a specific function.
    """
    for module in rhinoscriptsyntax_json:
        for func in module["functions"]:
            if func["Name"].lower() == function_name.lower():
                lines = [f"# {func['Name']}\n"]
                lines.append(f"**Module:** {module['ModuleName']}\n")

                sig = func.get("Signature", func["Name"] + "()")
                lines.append(f"## Signature\n```python\nrs.{sig}\n```\n")

                if func.get("Description"):
                    lines.append(f"## Description\n{func['Description']}\n")

                if func.get("ArgumentDesc"):
                    lines.append(f"## Parameters\n{func['ArgumentDesc']}\n")

                if func.get("Returns"):
                    lines.append(f"## Returns\n{func['Returns']}\n")

                if func.get("Example"):
                    examples = func["Example"]
                    if isinstance(examples, list):
                        example_code = "\n".join(examples)
                    else:
                        example_code = examples
                    lines.append(f"## Example\n```python\n{example_code}\n```\n")

                return "\n".join(lines)

    return f"Function '{function_name}' not found. Use search_rhinoscript_functions() to find functions."


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