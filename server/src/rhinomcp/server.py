# server.py
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError
import functools
import inspect
import re
import socket
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from rhinomcp.static.rhinoscriptsyntax import rhinoscriptsyntax_json
from rhinomcp.guidance import SERVER_INSTRUCTIONS

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
# Envelope metadata the plugin injects into a mutating command's result when
# perception is on. These are cross-cutting, not part of any single command's
# result contract, so they are stripped before post-flight validation; the
# full result, these keys included, is still returned to the caller.
PERCEPTION_RESULT_KEYS = ("_delta", "_health")
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
    "section_profile",
    "get_selected_objects_info",
    "get_document_summary",
    "get_objects",
    "capture_viewport",
    "get_commands",
    "describe_capabilities",
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


CAPABILITIES_COMMAND = "describe_capabilities"

# Server and plugin are released together but update on different schedules:
# `uvx rhinomcp@latest` re-resolves on every client launch, while the Package
# Manager updates the plugin on a Rhino restart. A plugin silently ignores
# parameters it has never heard of and answers an unknown command with a bare
# error, so the server checks the plugin actually connected before sending.
#
# When you add a parameter to an existing command, register it here with the
# plugin version that introduces it and the value that means "not used".
PARAMS_SINCE: Dict[str, Dict[str, tuple]] = {
    "sweep1": {"cap_planar_ends": ("0.4.0", False)},
}
# Commands added after describe_capabilities (0.3.2) existed, so a plugin too
# old to report its command table is still refused with the right advice.
COMMANDS_SINCE: Dict[str, str] = {
    "create_planar_region": "0.4.0",
}
PLUGIN_UPDATE_ADVICE = (
    "Update rhinomcp in Rhino's Package Manager (Tools > Package Manager > "
    "Installed), then restart Rhino and run mcpstart."
)
SERVER_UPDATE_ADVICE = (
    "Restart the MCP client so `uvx rhinomcp@latest` picks up the newer server, "
    "or run `uv tool upgrade rhinomcp` if it is installed as a tool."
)
_VERSION_PREFIX = re.compile(r"\s*v?(\d+(?:\.\d+)*)")
_UNKNOWN_COMMAND_ANSWER = re.compile(r"^Unknown command( type)?\b")


def server_version() -> str | None:
    """This package's installed version, or None outside an installed package."""
    try:
        return _pkg_version("rhinomcp")
    except PackageNotFoundError:
        return None


def parse_version(text) -> tuple | None:
    """The leading dotted integers, retaining nonzero revisions, or None.

    "0.4.0", "0.4.0.0" and "0.4.0+abc" all read as (0, 4, 0); "unknown" as None.
    """
    match = _VERSION_PREFIX.match(str(text)) if text else None
    if not match:
        return None
    parts = [int(part) for part in match.group(1).split(".")]
    while len(parts) > 3 and parts[-1] == 0:
        parts.pop()
    return tuple(parts + [0] * (3 - len(parts)))


def version_skew_report(plugin_version) -> Dict[str, Any]:
    """Compare the plugin's reported version with this server's.

    Returns server_version, plugin_matches_server (None when either side is
    unknown) and update_advice naming the older side, or None when they match.
    """
    server = server_version()
    report: Dict[str, Any] = {
        "server_version": server,
        "plugin_matches_server": None,
        "update_advice": None,
    }
    plugin, mine = parse_version(plugin_version), parse_version(server)
    if plugin is None or mine is None:
        return report
    report["plugin_matches_server"] = plugin == mine
    if plugin < mine:
        report["update_advice"] = (
            f"The Rhino plugin ({plugin_version}) is older than this server "
            f"({server}). {PLUGIN_UPDATE_ADVICE}"
        )
    elif plugin > mine:
        report["update_advice"] = (
            f"This server ({server}) is older than the Rhino plugin "
            f"({plugin_version}). {SERVER_UPDATE_ADVICE}"
        )
    return report


def unsupported_command_message(command_type: str, plugin_version: str, since) -> str:
    """Actionable text for a command the connected plugin cannot run."""
    added = f", which was added in plugin {since}" if since else ""
    return (
        f"The connected rhinomcp plugin ({plugin_version}) does not support "
        f"'{command_type}'{added}; this server is {server_version() or 'unknown'}. "
        f"{PLUGIN_UPDATE_ADVICE}"
    )


class UnsupportedCommandError(Exception):
    """The connected plugin cannot run this command; the socket itself is fine."""


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


def _normalize_negative_zero(value: Any) -> Any:
    """Remove signed zero from decoded results for strict MCP JSON clients.

    JavaScript JSON serialization loses the sign of -0.0. Normalize only zero,
    preserving nonzero measurements and strings containing serialized user data.
    """
    if isinstance(value, float):
        return 0.0 if value == 0.0 else value
    if isinstance(value, dict):
        return {key: _normalize_negative_zero(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_negative_zero(item) for item in value]
    return value


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
        # Commands the plugin on the other end of this socket says it can preview.
        # None means "not asked yet"; connecting and dropping both reset it, so an
        # answer from one plugin is never reused for another.
        self._dry_run_commands: set[str] | None = None
        # The plugin's whole describe_capabilities answer, read once per socket:
        # None until read; {} when the plugin definitively has no such command.
        self._capabilities: Dict[str, Any] | None = None
        self._capabilities_lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to the Rhino addon socket server"""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self._dry_run_commands = None
            self._capabilities = None
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
                self._dry_run_commands = None
                self._capabilities = None

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
        across concurrent callers so request/response framing isn't interleaved.

        Before a command leaves the client it is checked against the plugin
        actually connected (see _check_plugin_compatibility); the capabilities
        read that check relies on is itself exempt so it cannot recurse.
        """
        params = params or {}
        self._preflight_validate(command_type, params)
        if command_type != CAPABILITIES_COMMAND:
            self._check_plugin_compatibility(command_type, params)
        with self._send_lock:
            return self._send_command_locked(command_type, params)

    def _preflight_validate(self, command_type: str, params: Dict[str, Any]):
        """Validate params against the JSON Schema contract before anything
        touches the socket. In 'warn' mode log and continue (safe default); in
        'strict' raise so the bad payload never reaches Rhino. validate_command
        no-ops if jsonschema is missing or the command has no schema yet.
        """
        if RHINO_VALIDATE == "off":
            return
        from rhinomcp.validation import validate_command

        try:
            validate_command(command_type, params, raise_on_error=True)
        except Exception as ve:
            # validate_command raises jsonschema.ValidationError on schema
            # failures (FileNotFoundError is handled internally). The broad
            # except keeps a missing jsonschema install from needing an import
            # here; the only expected type is ValidationError.
            if RHINO_VALIDATE == "strict":
                raise ValueError(f"Invalid params for '{command_type}': {ve}") from ve
            logger.warning(f"Pre-flight validation failed for {command_type}: {ve}")

    def _check_plugin_compatibility(self, command_type: str, params: Dict[str, Any]):
        """Refuse what the connected plugin cannot do, before the socket send.

        All three checks read the plugin's own describe_capabilities answer,
        fetched once per connection:

        - a command the plugin does not list is refused with update advice
          instead of being forwarded to a bare "Unknown command type" error;
        - a PARAMS_SINCE parameter that is actually used is refused when the
          plugin predates it, or when its version could not be read, because a
          plugin silently ignores parameters it does not know;
        - dry_run keeps its explicit opt-in gate.
        """
        capabilities = self._plugin_capabilities()
        version_text = self._plugin_version_text()
        since = COMMANDS_SINCE.get(command_type)

        if capabilities == {}:
            # Definitive: the plugin predates describe_capabilities, so it also
            # predates everything registered in the tables above.
            if since:
                raise UnsupportedCommandError(
                    unsupported_command_message(command_type, version_text, since)
                )
        elif capabilities:
            advertised = {
                entry.get("name")
                for entry in capabilities.get("commands", [])
                if isinstance(entry, dict)
            }
            if advertised and command_type not in advertised:
                raise UnsupportedCommandError(
                    unsupported_command_message(command_type, version_text, since)
                )

        for name, (introduced, unused) in PARAMS_SINCE.get(command_type, {}).items():
            value = params.get(name)
            if value is None or value == unused:
                continue
            if capabilities is None:
                raise Exception(
                    "Could not read the plugin's capabilities, so support for "
                    f"'{name}' on '{command_type}' cannot be confirmed and an older "
                    "plugin would silently ignore it. The command was not sent. "
                    f"Retry, or call without {name}."
                )
            plugin = (
                parse_version(capabilities.get("version")) if capabilities else None
            )
            if plugin is None or plugin < parse_version(introduced):
                raise Exception(
                    f"'{command_type}' parameter '{name}' needs plugin {introduced}; "
                    f"the connected rhinomcp plugin ({version_text}) would silently "
                    f"ignore it. The command was not sent. {PLUGIN_UPDATE_ADVICE} "
                    f"Or call without {name}."
                )

        if params.get("dry_run"):
            self._require_dry_run_support(command_type, capabilities)

    def _require_dry_run_support(self, command_type: str, capabilities):
        """Refuse a preview the connected plugin cannot give.

        Server and plugin ship separately, so a new server can meet an old
        plugin. That plugin drops the dry_run param it has never heard of, runs
        the real boolean, and deletes the source objects, while the caller reads
        the reply as a preview. So the check happens here, before the send, and
        only an explicit yes lets the command through: a command the list doesn't
        mention, an entry without the field, or an unreadable answer is a no.
        """
        if capabilities and command_type in (self._dry_run_commands or set()):
            return

        raise Exception(
            "The installed rhinomcp plugin does not report dry_run support for "
            f"'{command_type}', so a preview would run as the real operation and "
            "could delete the source objects. The command was not sent. Update "
            "the plugin to match this server version, or retry without dry_run."
        )

    def _plugin_capabilities(self) -> Dict[str, Any] | None:
        """The connected plugin's describe_capabilities answer, read once per
        connection and dropped with the socket, since the next socket may reach
        a different plugin.

        Returns the answer; {} when the plugin definitively has no such command
        (it predates 0.3.2); None when the read failed for another reason (a
        dropped frame, a timeout). A failure is not remembered, so the next
        command asks again instead of the connection being stuck on a socket
        that merely hiccuped. The read sends no gated parameters of its own.
        """
        with self._capabilities_lock:
            if self._capabilities is None:
                try:
                    answer = self.send_command(CAPABILITIES_COMMAND, {})
                except UnsupportedCommandError:
                    answer = {}
                except Exception as e:
                    logger.warning(
                        f"Could not read the plugin's capabilities ({str(e)}); "
                        "the next command will ask again."
                    )
                    return None
                if not isinstance(answer, dict):
                    answer = {}
                self._capabilities = answer
                self._dry_run_commands = {
                    entry.get("name")
                    for entry in answer.get("commands", [])
                    if isinstance(entry, dict) and entry.get("supports_dry_run") is True
                }
                advice = version_skew_report(answer.get("version"))["update_advice"]
                if answer and advice:
                    logger.warning(f"Version skew: {advice}")
            return self._capabilities

    def _plugin_version_text(self) -> str:
        """The plugin version for messages, or what is known in its place."""
        if self._capabilities is None:
            return "version not read"
        if not self._capabilities:
            return "older than 0.3.2"
        return str(self._capabilities.get("version") or "unknown version")

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
                message = response.get("message", "Unknown error from Rhino")
                logger.error(f"Rhino error: {message}")
                if _UNKNOWN_COMMAND_ANSWER.match(message):
                    # An old plugin cannot list its commands, so this is where
                    # its refusal is turned into something a person can act on.
                    raise UnsupportedCommandError(
                        unsupported_command_message(
                            command_type,
                            self._plugin_version_text(),
                            COMMANDS_SINCE.get(command_type),
                        )
                    )
                raise Exception(message)

            result = _normalize_negative_zero(response.get("result", {}))

            # Post-flight: validate the unwrapped result against the response
            # contract, mirroring the pre-flight semantics. The C# side doesn't
            # validate anything against contracts/, so this is the only place
            # plugin/contract drift gets caught. Note the command has already
            # executed in Rhino by now: 'warn' logs and returns the result
            # anyway; 'strict' raises. validate_response no-ops if jsonschema
            # is missing or the command has no response schema.
            if RHINO_VALIDATE != "off":
                from rhinomcp.validation import HAS_JSONSCHEMA, validate_response

                # Validate the command's own result, not the perception envelope
                # the plugin may have injected into it. _delta / _health are
                # metadata no response schema declares, so leaving them in would
                # trip a closed (additionalProperties:false) schema such as
                # object_attributes and fail an otherwise-correct response.
                to_validate = result
                if isinstance(result, dict) and any(
                    key in result for key in PERCEPTION_RESULT_KEYS
                ):
                    to_validate = {
                        key: value
                        for key, value in result.items()
                        if key not in PERCEPTION_RESULT_KEYS
                    }

                try:
                    validate_response(command_type, to_validate, raise_on_error=True)
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
        except UnsupportedCommandError:
            # The plugin answered; the socket is healthy. Propagate as-is.
            raise
        except Exception as e:
            logger.error(f"Error communicating with Rhino: {str(e)}")
            # Don't try to reconnect here - let the get_rhino_connection handle reconnection
            self.disconnect()
            raise Exception(f"Communication error with Rhino: {str(e)}")


@asynccontextmanager
async def server_lifespan(server: MCPServer) -> AsyncIterator[Dict[str, Any]]:
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


def _reporting_errors(fn):
    """Re-raise a tool's failure as ToolError so its message reaches the client.

    MCP SDK 2.x reports any other exception to the client as only
    "Error executing tool <name>". RhinoMCP's error text is the agent's recovery
    path (start Rhino and run `mcpstart`, fix a parameter, retry after a dropped
    connection), so it has to survive the trip. Only the callable handed to the
    SDK is wrapped; the module-level tool function keeps raising its own types.
    """
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except (ToolError, MCPError):
                raise
            except Exception as e:
                raise ToolError(str(e)) from e

        return async_wrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ToolError, MCPError):
            raise
        except Exception as e:
            raise ToolError(str(e)) from e

    return wrapper


class RhinoMCPServer(MCPServer):
    """MCPServer whose tools report their real error messages to the client."""

    def add_tool(self, fn, *args, **kwargs):
        return super().add_tool(_reporting_errors(fn), *args, **kwargs)


# Create the MCP server with lifespan support
mcp = RhinoMCPServer(
    "RhinoMCP", lifespan=server_lifespan, instructions=SERVER_INSTRUCTIONS
)


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
