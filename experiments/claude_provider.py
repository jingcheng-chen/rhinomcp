"""Restricted Claude Code session adapter; requires local authentication.

Raw provider events are retained beside normalized workflow telemetry. This is
not an OS sandbox. Live interoperability must be validated before comparisons.
"""

import json
import os
import signal
import subprocess
import time

import jsonschema


def gateway_config(config):
    # Existing gateways supply TOML values to Codex. Parse them, never eval them.
    # The optional Claude adapter requires Python 3.11+ for the stdlib parser.
    import tomllib

    parsed = tomllib.loads(
        "\n".join(f"{key} = {value}" for key, value in config.items())
    )
    if set(parsed) - {"command", "args", "cwd", "env", "required", "tools"}:
        raise ValueError("Unsupported gateway configuration")
    if not isinstance(parsed.get("command"), str) or not isinstance(
        parsed.get("args"), list
    ):
        raise ValueError("Explicit local gateway command and arguments required")
    names = []
    for name, rule in parsed.get("tools", {}).items():
        if (
            set(rule) != {"approval_mode"}
            or rule["approval_mode"] != "approve"
            or not name.replace("_", "").isalnum()
        ):
            raise ValueError("Only explicit approved gateway tools are supported")
        names.append("mcp__rhino_experiment__" + name)
    if not names:
        raise ValueError("An explicit tool allowlist is required")
    return {
        "mcpServers": {
            "rhino_experiment": {
                key: parsed[key]
                for key in ("command", "args", "cwd", "env")
                if key in parsed
            }
        }
    }, names


def normalize(raw, target, allowed):
    """Preserve unique call IDs; an unanswered call remains unfinished."""
    calls, completed, emitted = {}, set(), []
    result = None
    prefix = "mcp__rhino_experiment__"
    for line in raw.read_text().splitlines():
        event = json.loads(line)
        if event.get("parent_tool_use_id"):
            raise RuntimeError("Unexpected child-agent event")
        for block in event.get("message", {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                name, call_id = block["name"], block["id"]
                if name == "StructuredOutput":
                    continue  # Provider's schema mechanism, not an MCP call.
                if name not in allowed or not name.startswith(prefix):
                    raise RuntimeError("Provider used an unapproved tool")
                item = {
                    "id": call_id,
                    "type": "mcp_tool_call",
                    "tool": name[len(prefix) :],
                    "arguments": block["input"],
                }
                if call_id in calls:
                    if calls[call_id] != item:
                        raise RuntimeError(
                            "Provider reused a tool ID with different input"
                        )
                    continue
                calls[call_id] = item
                emitted.append({"type": "item.started", "item": item})
            elif (
                block.get("type") == "tool_result" and block.get("tool_use_id") in calls
            ):
                call_id = block["tool_use_id"]
                if call_id in completed:
                    raise RuntimeError("Duplicate provider tool result")
                completed.add(call_id)
                failed = block.get("is_error", False)
                emitted.append(
                    {
                        "type": "item.completed",
                        "item": {
                            **calls[call_id],
                            "status": "failed" if failed else "completed",
                            "result": {
                                "isError": failed,
                                "content": block.get("content"),
                            },
                        },
                    }
                )
        if event.get("type") == "result":
            if result is not None:
                raise RuntimeError("Multiple provider result events")
            result = event
            emitted.append(
                {
                    "type": "turn.completed",
                    "usage": event.get("usage"),
                    "provider": "claude",
                }
            )
    target.write_text("".join(json.dumps(event) + "\n" for event in emitted))
    return result


def run(directory, prompt, output_schema, timeout, mcp_config, agent_config):
    from experiments.runner import save

    if (
        set(agent_config) != {"provider", "model", "reasoning_effort"}
        or agent_config["provider"] != "claude"
    ):
        raise ValueError("Explicit Claude provider/model/effort required")
    if (
        not isinstance(agent_config["model"], str)
        or not agent_config["model"].strip()
        or agent_config["reasoning_effort"] not in {"low", "medium", "high", "xhigh"}
    ):
        raise ValueError("Unsupported Claude model/effort configuration")
    gateway, allowed = gateway_config(mcp_config or {})
    auth = subprocess.run(
        ["claude", "auth", "status", "--json"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    status = json.loads(auth.stdout)
    if status.get("loggedIn") is not True:
        raise RuntimeError(
            "Claude Code is signed out; sign in locally before a session"
        )
    directory.mkdir()
    (directory / "prompt.txt").write_text(prompt)
    save(directory / "schema.json", output_schema)
    save(directory / "mcp.json", gateway)
    command = [
        "claude",
        "--print",
        "--verbose",
        "--restricted",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        str(directory / "mcp.json"),
        "--allowedTools",
        ",".join(allowed),
        "--permission-mode",
        "dontAsk",
        "--permission-prompts",
        "none",
        "--setting-sources",
        "",
        "--settings",
        '{"disableAllHooks":true,"enabledPlugins":{}}',
        "--disable-slash-commands",
        "--no-chrome",
        "--no-session-persistence",
        "--output-format",
        "stream-json",
        "--json-schema",
        json.dumps(output_schema),
        "--model",
        agent_config["model"],
        "--effort",
        agent_config["reasoning_effort"],
    ]
    save(
        directory / "invocation.json",
        {
            "command": command,
            "timeout_seconds": timeout,
            "provider": "claude",
            "version": subprocess.check_output(
                ["claude", "--version"], text=True
            ).strip(),
        },
    )
    started, outcome = time.monotonic(), "failed"
    raw = directory / "provider-events.jsonl"
    try:
        with raw.open("w") as events, (directory / "stderr.log").open("w") as errors:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=events,
                stderr=errors,
                text=True,
                cwd=directory,
                start_new_session=True,
            )
            try:
                proc.communicate(prompt, timeout=timeout)
            except BaseException:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise
        result = normalize(raw, directory / "events.jsonl", allowed)
        if (
            proc.returncode
            or result is None
            or result.get("is_error")
            or result.get("subtype") != "success"
        ):
            raise RuntimeError(
                "Claude session failed; inspect retained provider events"
            )
        output = result.get("structured_output")
        jsonschema.validate(output, output_schema)
        save(directory / "result.json", output)
        outcome = "completed"
        return output
    except subprocess.TimeoutExpired:
        outcome = "timed_out"
        raise
    finally:
        if raw.exists() and not (directory / "events.jsonl").exists():
            try:
                normalize(raw, directory / "events.jsonl", allowed)
            except (ValueError, RuntimeError) as error:
                save(directory / "telemetry-error.json", {"error": str(error)})
        save(
            directory / "status.json",
            {
                "status": outcome,
                "elapsed_seconds": time.monotonic() - started,
                "provider": "claude",
            },
        )
