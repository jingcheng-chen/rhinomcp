# Using RhinoMCP from another computer

RhinoMCP is designed for an AI client and Rhino on the same machine. This guide
covers the common case where they are not: the AI client runs on one computer
(for example a Mac) and Rhino 8 runs on a Windows PC on the same network.

The Rhino plugin only listens on `127.0.0.1:1999`, and the bridge has no
authentication, so the PC should not expose that port to the network. Both
setups below use SSH instead: SSH provides encryption and key authentication,
and Rhino's port stays on loopback.

| | Option 1: run the server over SSH | Option 2: SSH port forward |
|---|---|---|
| Where `rhinomcp` runs | On the Windows PC | On the client computer |
| What to keep running | Nothing. The client starts `ssh` per session | An `ssh -L` tunnel |
| Needs on Windows | OpenSSH Server, `uv`, `rhinomcp` | OpenSSH Server |
| Cleanup | Both ends exit when the client session ends | You stop the tunnel yourself |

Option 1 is simpler to operate. Option 2 keeps all Python on the client
computer.

Tested with a macOS client, Windows 10 22H2, Rhino 8.35, rhinomcp 0.4.1.1 and
Codex CLI 0.155.1. Other clients that launch stdio MCP servers should work the
same way.

## Prepare Windows: OpenSSH Server

Both options need an SSH login from the client to the Windows PC with a key.
Run these in an elevated PowerShell on Windows.

1. Install and start the server:

   ```powershell
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Start-Service sshd
   Set-Service -Name sshd -StartupType Automatic
   ```

   If `Add-WindowsCapability` hangs (it downloads from Windows Update, which a
   disabled update service or WSUS can block), use **Settings → Optional
   features** or `winget install Microsoft.OpenSSH.Beta`.

2. Allow inbound SSH. Without this rule the PC looks the same as one with no
   SSH server at all:

   ```powershell
   New-NetFirewallRule -Name sshd -DisplayName "OpenSSH Server (sshd)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
   ```

   Windows drops ping by default, so test reachability with the port
   (`nc -vz <pc-address> 22`), not `ping`.

3. Install the client's public key. **Where it goes depends on the Windows
   account:**

   - Standard user: `C:\Users\<user>\.ssh\authorized_keys`.
   - Member of Administrators: `C:\ProgramData\ssh\administrators_authorized_keys`.
     `sshd` ignores the per-user file for these accounts. It also silently
     ignores this file unless only Administrators and SYSTEM can access it:

     ```powershell
     $f = "$env:ProgramData\ssh\administrators_authorized_keys"
     icacls $f /reset
     icacls $f /inheritance:r /grant "*S-1-5-32-544:F" "*S-1-5-18:F"
     icacls $f   # must list exactly two entries
     ```

     The SIDs avoid localized group names such as `Administratoren`.
     `/reset` first makes the result the same no matter what the file's ACL
     was before.

   A key that `sshd` ignores looks exactly like a missing key: SSH falls back
   to asking for a password.

On the client, add a host entry to `~/.ssh/config`. The key name is an example;
`IdentitiesOnly` stops SSH from offering other keys first:

```
Host rhino-pc
    HostName <pc-address>
    User <windows-user>
    IdentityFile ~/.ssh/id_ed25519_rhino
    IdentitiesOnly yes
    ConnectTimeout 10
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

Then run `ssh rhino-pc` once by hand to accept the host key. The setups below
use `BatchMode=yes`, which makes SSH fail instead of waiting on a prompt no one
can see, so the first host-key confirmation has to happen here.

## Option 1: run the server on Windows over SSH

The client launches `ssh`, and `ssh` runs `rhinomcp` on the PC. MCP messages
travel over the SSH session's stdin and stdout, and `rhinomcp` connects to Rhino
on the PC's own loopback.

```
AI client ──stdio──► ssh ═══SSH═══► rhinomcp.exe ──127.0.0.1:1999──► Rhino plugin
```

1. Install `uv` and the server on Windows. Pin the server to the same version
   as the Rhino plugin:

   ```sh
   ssh rhino-pc 'powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"'
   ssh rhino-pc 'C:\Users\<windows-user>\.local\bin\uv.exe tool install rhinomcp==<plugin-version>'
   ```

   This gives you `C:\Users\<windows-user>\.local\bin\rhinomcp.exe`. Use that
   absolute path below. The SSH session's `PATH` may not include it.

2. Point the client at `ssh`. For Codex (`~/.codex/config.toml`):

   ```toml
   [mcp_servers.rhino]
   command = "ssh"
   args = ["-T", "-o", "BatchMode=yes", "rhino-pc", "C:\\Users\\<windows-user>\\.local\\bin\\rhinomcp.exe"]
   startup_timeout_sec = 60
   ```

   For clients with an `mcpServers` JSON config:

   ```json
   {
     "mcpServers": {
       "rhino": {
         "command": "ssh",
         "args": ["-T", "-o", "BatchMode=yes", "rhino-pc", "C:\\Users\\<windows-user>\\.local\\bin\\rhinomcp.exe"]
       }
     }
   }
   ```

   `-T` keeps SSH from allocating a terminal, which would corrupt the stdio
   stream.

3. **Set server variables on the Windows side.** An `env` block in the client
   config only reaches the local `ssh` process. The default remote shell of
   Windows OpenSSH is `cmd`, so put the variables in the remote command:

   ```
   "set RHINO_MCP_TIMEOUT=30&& C:\\Users\\<windows-user>\\.local\\bin\\rhinomcp.exe"
   ```

   Leave no space before `&&`: `cmd` would keep it as part of the value. If you
   changed the default shell to PowerShell, use
   `$env:RHINO_MCP_TIMEOUT='30'; <path>` instead.

4. Run `mcpstart` in Rhino and start the client.

In testing, the first connection took about 3 seconds (SSH login plus Python
startup) and later tool calls took 0.1–0.3 seconds. When the client exits, or
its `ssh` process is killed, `rhinomcp` on the PC exits within seconds.

A network drop is different. If the connection disappears without being
closed (Wi-Fi turned off, cable pulled), the client's `ssh` gives up after
about a minute because of `ServerAliveInterval`, but by default the PC's `sshd`
never notices. `rhinomcp` and its Python processes keep running there. They do
not block new sessions, but they pile up if the network drops often. To make
`sshd` end such sessions, open `C:\ProgramData\ssh\sshd_config` in an elevated
editor and change these two commented lines:

```
#ClientAliveInterval 0
#ClientAliveCountMax 3
```

to:

```
ClientAliveInterval 15
ClientAliveCountMax 3
```

Change them where they are instead of adding them at the end: the default file
ends with a `Match Group administrators` block, and settings placed after it
apply only to administrators. Then check the file and restart the server in an
elevated PowerShell:

```powershell
& "$env:SystemRoot\System32\OpenSSH\sshd.exe" -t   # no output means the file is valid
Restart-Service sshd
```

In testing, with this setting the PC ended the session and its processes about
a minute after its Wi-Fi was turned off.

## Option 2: forward Rhino's port over SSH

`rhinomcp` runs on the client as usual. An SSH tunnel makes the PC's
`127.0.0.1:1999` appear on the client's `127.0.0.1:1999`.

```
AI client ──stdio──► rhinomcp ──127.0.0.1:1999──► ssh -L ═══SSH═══► 127.0.0.1:1999 ──► Rhino plugin
```

1. Start the tunnel and leave it running:

   ```sh
   ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes \
       -L 127.0.0.1:1999:127.0.0.1:1999 rhino-pc
   ```

   Write out **both** addresses:

   - **Local side:** if you leave out the local bind address
     (`-L 1999:localhost:1999`), SSH's `GatewayPorts` setting decides where it
     binds. With `GatewayPorts yes`, the unauthenticated Rhino bridge becomes
     reachable from the whole network, with no warning.
   - **Remote side:** the plugin listens on IPv4 only. If the PC resolves
     `localhost` to `::1`, the tunnel starts but every connection fails.

   Check the actual binding with `lsof -nP -iTCP:1999 -sTCP:LISTEN`. It must
   show `127.0.0.1:1999`, not `*:1999`.

2. Configure the client exactly as in the main README, keeping
   `RHINO_MCP_HOST=127.0.0.1`. Do **not** set `RHINO_MCP_ALLOW_REMOTE` for this.
   It only lets the server dial a non-loopback address; it does not change
   where the plugin listens.

If you change the local port, set `RHINO_MCP_PORT` to the same value. The remote
port stays `1999`. `ExitOnForwardFailure` only checks the local binding: a
wrong remote port still gives a running tunnel whose connections all fail.

## Troubleshooting

- **The client shows the server as connected, but tools fail.** The server
  starts even when Rhino is unreachable; the error appears on the first tool
  call: `Could not connect to Rhino at 127.0.0.1:1999. Please start Rhino, run
  the Rhino command mcpstart, then retry the MCP request.` Run `mcpstart` (once
  per Rhino session) and check the tunnel if you use Option 2. A read-only call
  such as `get_document_summary` is the only real end-to-end check.
- **`command not found` for `rhinomcp` or `uvx`.** Clients often start servers
  with a smaller `PATH` than your shell. Use absolute paths in the client
  config.
- **SSH asks for a password.** The key was not accepted. For an administrator
  account, check the file location and the `icacls` output above.
- **Nothing answers on port 22.** Check the firewall rule and that the `sshd`
  service is running.

## Security

RhinoMCP has no authentication of its own. Anyone who can use this SSH key can
run code on the PC in two ways:

- as the Windows account the key logs in to, with a shell; and
- through RhinoMCP's execution tools (`run_command`, Python, C#), which run
  inside Rhino with the rights of whoever is running Rhino.

So the SSH key, the login account and Rhino's own rights together are the
security boundary. Consider:

- **Log in with a dedicated standard (non-administrator) account.** Rhino can
  keep running in your own desktop account: the server reaches it over
  `127.0.0.1`, which every account on the PC shares. With Option 1, install `uv`
  and `rhinomcp` under the dedicated account and point the client at that
  account's `rhinomcp.exe`. An administrator account gets a fully elevated SSH
  session, and a key in `administrators_authorized_keys` works for every
  administrator on the PC.
- **Check that Rhino itself does not run elevated.** A dedicated account limits
  the shell, not the execution tools. With UAC on (the Windows default), Rhino
  started normally runs without administrator rights. If UAC is off (`EnableLUA`
  is `0` under
  `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System`) or Rhino is
  run as administrator, code sent through Rhino has full administrator rights,
  whichever account SSH uses.
- Keep the key on the client machine only, and do not sync it to cloud storage.
- Use the `RHINO_MCP_ENABLE_*` switches if you want fewer execution tools.
