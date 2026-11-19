# Security policy

## Reporting a vulnerability

Please don't report security problems in public issues. Use GitHub's private vulnerability
reporting instead: open the repository's **Security** tab and choose **Report a vulnerability**.
Include the version, the steps to reproduce, and what an attacker gains.

## Supported versions

Fixes go into the latest release only. The Python server (`rhinomcp` on PyPI), the Rhino plugin
(`rhinomcp` in Rhino's Package Manager) and the Claude Code plugin share one version number. Please
reproduce on the latest release before reporting.

## Threat model

RhinoMCP is a local tool. Know these properties before you run it:

- **The Rhino plugin listens on an unauthenticated TCP socket**, `127.0.0.1:1999` by default (or the
  port `mcpstart` reports). Any process on the same machine that can open a loopback connection can
  send it commands, including the script-execution commands. Run `mcpstop` when you aren't using it,
  and don't run it on a shared or multi-user machine.
- **Script execution is part of the design.** `run_command`, `execute_rhinoscript_python_code` and
  `execute_rhinocommon_csharp_code` run arbitrary code inside Rhino with your user's permissions.
  Document changes are recorded as an undo step; anything else a script does (files, network,
  processes) is not reversible.
- **The `RHINO_MCP_ENABLE_*` switches are enforced by the Python server only.** They keep your AI
  client from calling those tools. They don't stop a process that talks to the plugin's socket
  directly.
- **Don't expose the socket beyond loopback.** `RHINO_MCP_ALLOW_REMOTE=1` lets the server connect
  to a non-loopback host, but the link is plaintext and unauthenticated.
- **Document content reaches the model.** Object names, layer names, user strings and Grasshopper
  values are returned to the AI model as tool output. A `.3dm` or `.gh` file from someone else can
  carry text written to steer the agent (prompt injection). Be careful about letting an agent run
  scripts while such a file is open.
- **Model data leaves your machine.** Geometry, layer structure, file names and viewport captures go
  to your AI model provider as part of normal use. Check that this is allowed for NDA or
  export-controlled work.

Known open items from the July 2026 audit are tracked in issue #48.
