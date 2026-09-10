"""Server and plugin update on different schedules, so the server checks the
plugin it is actually talking to instead of assuming the two match.

A plugin ignores parameters it has never heard of and answers an unknown command
with a bare error; both would otherwise reach the agent as silently wrong
results or as a message with no way forward.
"""

import json
import logging
import socket
from unittest.mock import MagicMock, patch

import pytest

IDS = [
    "12345678-1234-1234-1234-123456789012",
    "87654321-4321-4321-4321-210987654321",
]
ADVERTISED = [
    {"name": "boolean_union", "read_only": False, "supports_dry_run": True},
    {"name": "sweep1", "read_only": False},
]
DONE = {"result_ids": [IDS[0]], "count": 1, "message": "created 1 object(s)"}


def frame(payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "big") + payload


def buffered_recv(wire_bytes: bytes):
    buffer = bytearray(wire_bytes)

    def recv(n):
        chunk = bytes(buffer[:n])
        del buffer[:n]
        return chunk

    return recv


def capabilities(commands, version="0.4.0"):
    return frame(
        json.dumps(
            {
                "status": "success",
                "result": {
                    "version": version,
                    "command_count": len(commands),
                    "commands": commands,
                    "perception": {"description": "none", "envelope_flags": []},
                },
            }
        ).encode("utf-8")
    )


def success(result):
    return frame(json.dumps({"status": "success", "result": result}).encode("utf-8"))


def error(message):
    return frame(json.dumps({"status": "error", "message": message}).encode("utf-8"))


def connected(mock_socket_class, wire):
    from rhinomcp.server import RhinoConnection

    mock_sock = MagicMock()
    mock_sock.recv.side_effect = buffered_recv(wire)
    mock_socket_class.return_value = mock_sock
    conn = RhinoConnection(host="127.0.0.1", port=1999)
    conn.connect()
    return conn, mock_sock


def sent_types(mock_sock):
    return [json.loads(c.args[0][4:])["type"] for c in mock_sock.sendall.call_args_list]


class TestUnsupportedCommands:
    @patch("socket.socket")
    def test_command_missing_from_the_plugins_table_is_refused_with_advice(
        self, mock_socket_class
    ):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED, "0.3.2")
        )

        with pytest.raises(
            Exception,
            match=r"\(0\.3\.2\) does not support 'create_planar_region', which was "
            r"added in plugin 0\.4\.0.*Package Manager",
        ):
            conn.send_command("create_planar_region", {"boundary_ids": IDS})

        assert sent_types(mock_sock) == ["describe_capabilities"]

    @patch("socket.socket")
    def test_plugin_without_describe_capabilities_is_told_to_update(
        self, mock_socket_class
    ):
        conn, mock_sock = connected(
            mock_socket_class, error("Unknown command type: describe_capabilities")
        )

        with pytest.raises(
            Exception,
            match=r"\(older than 0\.3\.2\) does not support 'create_planar_region'"
            r".*Package Manager",
        ):
            conn.send_command("create_planar_region", {"boundary_ids": IDS})

        assert sent_types(mock_sock) == ["describe_capabilities"]

    @patch("socket.socket")
    def test_an_old_plugins_unknown_command_answer_is_rewritten(
        self, mock_socket_class
    ):
        """An old plugin cannot list its commands, so a command outside the
        since-table still goes out; its refusal comes back actionable and the
        socket survives, because the plugin did answer."""
        conn, mock_sock = connected(
            mock_socket_class,
            error("Unknown command type: describe_capabilities")
            + error("Unknown command type: boolean_union"),
        )

        with pytest.raises(
            Exception,
            match=r"\(older than 0\.3\.2\) does not support 'boolean_union'; this "
            r"server is .*Package Manager",
        ) as info:
            conn.send_command("boolean_union", {"object_ids": IDS})

        assert not str(info.value).startswith("Communication error")
        assert sent_types(mock_sock) == ["describe_capabilities", "boolean_union"]
        assert conn.sock is not None

    @patch("socket.socket")
    def test_capabilities_are_read_once_per_connection(self, mock_socket_class):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED) + success(DONE) + success(DONE)
        )

        conn.send_command("boolean_union", {"object_ids": IDS})
        conn.send_command("boolean_union", {"object_ids": IDS})

        assert sent_types(mock_sock) == [
            "describe_capabilities",
            "boolean_union",
            "boolean_union",
        ]


class TestParametersOlderPluginsWouldDrop:
    SWEEP = {
        "rail_id": IDS[0],
        "profile_ids": [IDS[1]],
        "closed": False,
        "cap_planar_ends": True,
    }

    @patch("socket.socket")
    def test_refused_when_the_plugin_predates_the_parameter(self, mock_socket_class):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED, "0.3.2")
        )

        with pytest.raises(
            Exception,
            match=r"'cap_planar_ends' needs plugin 0\.4\.0; the connected rhinomcp "
            r"plugin \(0\.3\.2\) would silently ignore it.*Package Manager",
        ):
            conn.send_command("sweep1", self.SWEEP)

        assert sent_types(mock_sock) == ["describe_capabilities"]

    @patch("socket.socket")
    def test_sent_when_the_plugin_is_new_enough(self, mock_socket_class):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED, "0.4.0") + success(DONE)
        )

        assert conn.send_command("sweep1", self.SWEEP) == DONE
        assert sent_types(mock_sock) == ["describe_capabilities", "sweep1"]

    @patch("socket.socket")
    def test_a_four_part_assembly_version_counts_as_new_enough(self, mock_socket_class):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED, "0.4.0.0") + success(DONE)
        )

        assert conn.send_command("sweep1", self.SWEEP) == DONE

    @patch("socket.socket")
    def test_an_unused_parameter_does_not_block_an_old_plugin(self, mock_socket_class):
        conn, mock_sock = connected(
            mock_socket_class, capabilities(ADVERTISED, "0.3.2") + success(DONE)
        )

        conn.send_command("sweep1", {**self.SWEEP, "cap_planar_ends": False})

        assert sent_types(mock_sock) == ["describe_capabilities", "sweep1"]

    @patch("socket.socket")
    def test_refused_when_support_cannot_be_confirmed_then_asks_again(
        self, mock_socket_class
    ):
        """A blip while reading capabilities is not an answer: the parameter is
        refused rather than silently dropped, and the next command asks again."""
        from rhinomcp.server import RhinoConnection

        serve = buffered_recv(capabilities(ADVERTISED, "0.4.0") + success(DONE))
        reads = []

        def recv(n):
            reads.append(n)
            if len(reads) == 1:
                raise socket.timeout("timed out")
            return serve(n)

        mock_sock = MagicMock()
        mock_sock.recv.side_effect = recv
        mock_socket_class.return_value = mock_sock
        conn = RhinoConnection(host="127.0.0.1", port=1999)
        conn.connect()

        with pytest.raises(Exception, match="cannot be confirmed"):
            conn.send_command("sweep1", self.SWEEP)

        assert conn.send_command("sweep1", self.SWEEP) == DONE
        assert sent_types(mock_sock) == [
            "describe_capabilities",
            "describe_capabilities",
            "sweep1",
        ]


class TestVersionSkew:
    def _run(self, mock_socket_class, caplog, server, plugin):
        with patch("rhinomcp.server.server_version", return_value=server):
            conn, _ = connected(
                mock_socket_class,
                capabilities(ADVERTISED, plugin) + success(DONE) + success(DONE),
            )
            with caplog.at_level(logging.WARNING, logger="RhinoMCPServer"):
                conn.send_command("boolean_union", {"object_ids": IDS})
                conn.send_command("boolean_union", {"object_ids": IDS})
        return [
            r.getMessage() for r in caplog.records if "Version skew" in r.getMessage()
        ]

    @patch("socket.socket")
    def test_an_older_plugin_is_reported_once_per_connection(
        self, mock_socket_class, caplog
    ):
        skew = self._run(mock_socket_class, caplog, server="0.4.0", plugin="0.3.2")

        assert len(skew) == 1
        assert "plugin (0.3.2) is older than this server (0.4.0)" in skew[0]
        assert "Package Manager" in skew[0]

    @patch("socket.socket")
    def test_an_older_server_points_at_its_launcher(self, mock_socket_class, caplog):
        skew = self._run(mock_socket_class, caplog, server="0.3.2", plugin="0.4.0")

        assert len(skew) == 1
        assert "server (0.3.2) is older than the Rhino plugin (0.4.0)" in skew[0]
        assert "uvx rhinomcp@latest" in skew[0]

    @patch("socket.socket")
    def test_matching_versions_are_quiet(self, mock_socket_class, caplog):
        assert (
            self._run(mock_socket_class, caplog, server="0.4.0", plugin="0.4.0") == []
        )

    @patch("rhinomcp.tools.describe_capabilities.get_rhino_connection")
    def test_describe_capabilities_reports_both_sides(self, mock_get_conn):
        from rhinomcp.tools.describe_capabilities import (
            describe_capabilities,
            version_skew_report,
        )

        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "version": "0.3.2",
            "command_count": 0,
            "commands": [],
            "perception": {"description": "none", "envelope_flags": []},
        }
        mock_get_conn.return_value = mock_conn

        # Other tests reload the server module; patch the helper retained by this tool.
        with patch.dict(version_skew_report.__globals__, server_version=lambda: "0.4.0"):
            result = describe_capabilities(ctx=None)

        assert result["version"] == "0.3.2"
        assert result["server_version"] == "0.4.0"
        assert result["plugin_matches_server"] is False
        assert "Package Manager" in result["update_advice"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0.4.0", (0, 4, 0)),
        ("0.4.0.0", (0, 4, 0)),
        ("0.4.0+abc123", (0, 4, 0)),
        ("0.0.0-mock", (0, 0, 0)),
        ("v1.2", (1, 2, 0)),
        ("unknown", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_version(text, expected):
    from rhinomcp.server import parse_version

    assert parse_version(text) == expected
