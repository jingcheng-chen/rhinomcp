# server.py
from mcp.server.fastmcp import FastMCP
import socket
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from rhinomcp.static.rhinoscriptsyntax import rhinoscriptsyntax_json

# Configuration from environment variables
RHINO_HOST = os.getenv("RHINO_MCP_HOST", "127.0.0.1")
RHINO_PORT = int(os.getenv("RHINO_MCP_PORT", "1999"))
# Sending arbitrary tool payloads (including run_command / execute_rhinoscript)
# over a non-loopback link with no authentication is genuinely dangerous.
# Refuse non-loopback connect targets unless the operator opts in explicitly.
RHINO_ALLOW_REMOTE = os.getenv("RHINO_MCP_ALLOW_REMOTE", "").lower() in (
    "1",
    "true",
    "yes",
)
if RHINO_HOST not in ("127.0.0.1", "::1", "localhost") and not RHINO_ALLOW_REMOTE:
    raise RuntimeError(
        f"RHINO_MCP_HOST={RHINO_HOST!r} is non-loopback. The TCP bridge to Rhino "
        "carries unauthenticated commands including arbitrary-code execution; "
        "set RHINO_MCP_ALLOW_REMOTE=1 to acknowledge the risk and proceed."
    )
RHINO_TIMEOUT = float(os.getenv("RHINO_MCP_TIMEOUT", "15.0"))
# Opt-in perception: when enabled, every mutating command carries an
# `include_delta` flag on the envelope, and the plugin attaches a `_delta` block
# (created_ids / deleted_ids / count_before / count_after) to the result so a
# client can see what changed without re-querying. Off by default, so responses
# are byte-identical unless explicitly turned on.
RHINO_PERCEPTION = os.getenv("RHINO_MCP_PERCEPTION", "").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
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
# Defer the unknown-value warning until after `logger` is defined; emitting it
# here would NameError before the server even starts.
_RHINO_VALIDATE_UNKNOWN = (
    RHINO_VALIDATE if RHINO_VALIDATE not in ("off", "warn", "strict") else None
)
if _RHINO_VALIDATE_UNKNOWN is not None:
    RHINO_VALIDATE = "warn"

# Configure logging
log_level = getattr(logging, RHINO_LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RhinoMCPServer")
logger.setLevel(log_level)

if _RHINO_VALIDATE_UNKNOWN is not None:
    logger.warning(
        f"Unknown RHINO_MCP_VALIDATE={_RHINO_VALIDATE_UNKNOWN!r}; falling back to 'warn'."
    )

if RHINO_DEBUG:
    logger.info("Debug mode enabled")


# Wire framing: every message in both directions is a 4-byte big-endian length
# header followed by that many bytes of UTF-8 JSON. The cap below bounds memory
# per frame; it also doubles as cross-version detection, since a legacy
# unframed response starts with '{' (0x7B) and would decode as a ~2 GB length.
FRAME_HEADER_SIZE = 4
MAX_FRAME_SIZE = 64 * 1024 * 1024


READONLY_RETRY_COMMANDS = {
    "get_object_info",
    "get_object_attributes",
    "analyze_objects",
    "measure_objects",
    "get_selected_objects_info",
    "get_document_summary",
    "get_objects",
    "capture_viewport",
    "get_commands",
    "gh_get_document_info",
    "gh_search_components",
    "gh_batch_search_components",
    "gh_list_component_categories",
    "gh_get_available_components",
    "gh_get_component_type_info",
    "gh_batch_get_component_type_info",
    "gh_get_graph",
    "gh_list_components",
    "gh_get_component_info",
    "gh_get_canvas_state",
    "gh_capture_preview",
    "gh_get_parameter_value",
}


class TransientRhinoConnectionError(ConnectionError):
    """A connected Rhino socket dropped while a command was in flight."""


def rhino_startup_error_message(
    host: str, port: int, prefix: str = "Could not connect to Rhino"
) -> str:
    """Actionable guidance for the common case where Rhino's TCP listener is not running."""
    return (
        f"{prefix} at {host}:{port}. "
        "Please start Rhino, run the Rhino command `mcpstart`, then retry the MCP request."
    )


@dataclass
class RhinoConnection:
    host: str
    port: int
    sock: socket.socket | None = (
        None  # Changed from 'socket' to 'sock' to avoid naming conflict
    )

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

    def _recv_exact(self, sock, num_bytes, buffer_size=8192):
        """Receive exactly num_bytes from sock.

        Raises ConnectionResetError if the peer closes mid-message; lets
        socket.timeout propagate so the caller's timeout handling applies.
        """
        received = bytearray()
        while len(received) < num_bytes:
            chunk = sock.recv(min(buffer_size, num_bytes - len(received)))
            if not chunk:
                raise ConnectionResetError(
                    "Connection closed mid-message "
                    f"({len(received)}/{num_bytes} bytes received)"
                )
            received.extend(chunk)
        return bytes(received)

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive one length-prefixed response frame.

        Every message on the wire is a 4-byte big-endian length header followed
        by that many bytes of UTF-8 JSON. Reading exact byte counts means
        message boundaries are never guessed: back-to-back responses can't
        bleed into one read, and a frame split across TCP segments is simply
        read until complete.
        """
        sock.settimeout(RHINO_TIMEOUT)

        header = self._recv_exact(sock, FRAME_HEADER_SIZE, buffer_size)
        if header.startswith(b"{"):
            # Bare JSON where a header should be: the installed plugin
            # predates framing. Fail actionably instead of treating '{"st'
            # as a ~2 GB length.
            raise Exception(
                "Rhino sent an unframed response: the installed rhinomcp "
                "plugin predates length-prefixed framing. Update the plugin "
                "to match this server version."
            )

        frame_length = int.from_bytes(header, "big")
        if frame_length <= 0 or frame_length > MAX_FRAME_SIZE:
            raise Exception(
                f"Invalid response frame length {frame_length} from Rhino "
                f"(limit {MAX_FRAME_SIZE} bytes)."
            )

        payload = self._recv_exact(sock, frame_length, buffer_size)
        logger.info(f"Received complete response ({len(payload)} bytes)")
        return payload

    def send_command(
        self, command_type: str, params: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """Send a command to Rhino and return the response. Thread-safe: serialized
        across concurrent callers so request/response framing isn't interleaved."""
        with self._send_lock:
            return self._send_command_locked(command_type, params)

    def _send_command_locked(
        self, command_type: str, params: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        attempts = 2 if command_type in READONLY_RETRY_COMMANDS else 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return self._send_command_once(command_type, params)
            except TransientRhinoConnectionError as e:
                last_error = e
                if attempt >= attempts:
                    raise
                logger.warning(
                    "Transient Rhino connection drop during read-only command "
                    f"{command_type}; retrying once."
                )
                self.disconnect()
                time.sleep(0.2)

        if last_error:
            raise last_error
        raise RuntimeError("Rhino command send failed without an error.")

    def _send_command_once(
        self, command_type: str, params: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        if not self.sock and not self.connect():
            raise ConnectionError(rhino_startup_error_message(self.host, self.port))

        command = {"type": command_type, "params": params or {}}
        if RHINO_PERCEPTION:
            # Envelope-level flags, kept out of params so they never collide with a
            # command's own parameters or trip params schema validation. The plugin
            # ignores them for read-only commands. Perception is the master switch
            # for the whole perceive-act loop: what changed (_delta) and whether the
            # new geometry is sound (_health).
            command["include_delta"] = True
            command["include_health"] = True

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
                    validate_command(
                        command_type, command["params"], raise_on_error=True
                    )
                except Exception as ve:
                    # validate_command raises jsonschema.ValidationError on schema
                    # failures (FileNotFoundError is handled internally). We keep
                    # the broad except so a missing jsonschema install doesn't
                    # require importing it here — but the only expected type is
                    # ValidationError.
                    msg = f"Pre-flight validation failed for {command_type}: {ve}"
                    if RHINO_VALIDATE == "strict":
                        raise ValueError(
                            f"Invalid params for '{command_type}': {ve}"
                        ) from ve
                    logger.warning(msg)

            if self.sock is None:
                raise Exception("Socket is not connected")

            # Send the command as one length-prefixed frame
            command_json = json.dumps(command)
            logger.debug(
                f"Raw command JSON ({len(command_json)} bytes): {command_json[:500]}..."
            )
            command_bytes = command_json.encode("utf-8")
            header = len(command_bytes).to_bytes(FRAME_HEADER_SIZE, "big")
            self.sock.sendall(header + command_bytes)
            logger.debug("Command sent, waiting for response...")

            # Set a timeout for receiving
            self.sock.settimeout(RHINO_TIMEOUT)

            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.sock)
            logger.debug(f"Received {len(response_data)} bytes of data")

            response = json.loads(response_data.decode("utf-8"))
            logger.info(f"Response status: {response.get('status', 'unknown')}")
            logger.debug(f"Full response: {json.dumps(response, indent=2)[:1000]}...")

            if response.get("status") == "error":
                logger.error(f"Rhino error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Rhino"))

            result = response.get("result", {})

            # Post-flight: validate the unwrapped result against the response
            # contract, mirroring the pre-flight semantics. The C# side doesn't
            # validate anything against contracts/, so this is the only place
            # plugin/contract drift gets caught. Note the command has already
            # executed in Rhino by now: 'warn' logs and returns the result
            # anyway; 'strict' raises. validate_response no-ops if jsonschema
            # is missing or the command has no response schema.
            if RHINO_VALIDATE != "off":
                from rhinomcp.validation import HAS_JSONSCHEMA, validate_response

                try:
                    validate_response(command_type, result, raise_on_error=True)
                except Exception as ve:
                    # Only a genuine validation verdict gets the warn/strict
                    # treatment. Anything else (unresolvable $ref, unreadable
                    # schema file) is a schema-infrastructure problem, not
                    # evidence the response is wrong — a successful command
                    # must not fail because the local schema tooling broke.
                    is_verdict = False
                    if HAS_JSONSCHEMA:
                        import jsonschema

                        is_verdict = isinstance(ve, jsonschema.ValidationError)
                    if not is_verdict:
                        logger.warning(
                            f"Could not validate response for {command_type} "
                            f"(schema error): {ve}"
                        )
                    elif RHINO_VALIDATE == "strict":
                        raise ValueError(
                            f"Rhino executed '{command_type}' but the response "
                            f"failed contract validation: {ve}"
                        ) from ve
                    else:
                        logger.warning(
                            f"Response validation failed for {command_type}: {ve}"
                        )

            return result
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Rhino")
            # Don't try to reconnect here - let the get_rhino_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.disconnect()
            raise Exception(
                "Timeout waiting for Rhino response - try simplifying your request"
            )
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.disconnect()
            raise TransientRhinoConnectionError(
                f"Connection to Rhino was interrupted at {self.host}:{self.port}. "
                "Retry the request. If this keeps happening, confirm Rhino is open "
                "and run the Rhino command `mcpstart`."
            ) from e
        except TransientRhinoConnectionError:
            raise
        except OSError as e:
            logger.error(f"Socket OS error: {str(e)}")
            self.disconnect()
            raise TransientRhinoConnectionError(
                f"Connection to Rhino was interrupted at {self.host}:{self.port}. "
                "Retry the request. If this keeps happening, confirm Rhino is open "
                "and run the Rhino command `mcpstart`."
            ) from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Rhino: {str(e)}")
            # Try to log what was received
            if "response_data" in locals() and response_data:  # type: ignore
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Rhino: {str(e)}")
        except ValueError:
            # Pre/post-flight validation failures — local, not a transport
            # issue. Propagate.
            raise
        except Exception as e:
            logger.error(f"Error communicating with Rhino: {str(e)}")
            # Don't try to reconnect here - let the get_rhino_connection handle reconnection
            self.disconnect()
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
            get_rhino_connection()
            logger.info("Successfully connected to Rhino on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Rhino on startup: {str(e)}")
            logger.warning(rhino_startup_error_message(RHINO_HOST, RHINO_PORT))

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
mcp = FastMCP("RhinoMCP", lifespan=server_lifespan)


# ============================================================================
# MCP Resources - Browsable RhinoScript Documentation
# ============================================================================


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
                raise Exception(rhino_startup_error_message(RHINO_HOST, RHINO_PORT))
            logger.info("Created new persistent connection to Rhino")

        return _rhino_connection


# Main execution
def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
