#!/bin/bash
# Build the rhinomcp plugin and install it into the Mac user-level Rhino
# plug-ins directory.
#
# Per the McNeel guide
# (https://developer.rhino3d.com/guides/rhinocommon/your-first-plugin-mac/), Rhino
# for Mac loads user plug-ins from
# ~/Library/Application Support/McNeel/Rhinoceros/<ver>/Plug-ins/. The first time
# you install, drag the .rhp onto a running Rhino window so Rhino registers the
# path — afterwards every rebuild just refreshes the files in place and Rhino
# picks up the new build on next launch.
#
# Usage:
#   ./install.sh                          # Release build, default user dir
#   CONFIG=Debug ./install.sh             # Debug build (symbols, no optimization)
#   RHINO_VERSION=8.0 ./install.sh        # target a specific Rhino version dir
#   RHINO_PLUGIN_DIR=/path ./install.sh   # override the install location entirely
#
# Note: this is the Mac-only dev install path. The csproj's
# CopyToRhinoPluginDir=true target is an alternate workflow that drops the .rhp
# (without its dependent dlls) into the app bundle; prefer this script unless
# you know you need that.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLN="$SCRIPT_DIR/rhinomcp.sln"
CONFIG="${CONFIG:-Release}"
RHINO_VERSION="${RHINO_VERSION:-8.0}"
RHINO_PLUGIN_DIR="${RHINO_PLUGIN_DIR:-$HOME/Library/Application Support/McNeel/Rhinoceros/$RHINO_VERSION/Plug-ins/rhinomcp}"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "error: this script targets macOS. On Windows, use the csproj directly." >&2
  exit 1
fi

if [[ ! -f "$SLN" ]]; then
  echo "error: solution not found at $SLN" >&2
  exit 1
fi

if ! command -v dotnet >/dev/null 2>&1; then
  echo "error: dotnet CLI not found. Install the .NET 8 SDK from https://dotnet.microsoft.com/" >&2
  exit 1
fi

if pgrep -qi "^Rhinoceros$|^Rhino$"; then
  echo "warning: Rhino appears to be running. Its loaded dlls are locked, so the"
  echo "         install step may fail mid-copy. Quit Rhino if rsync errors below."
  echo
fi

echo "==> building rhinomcp ($CONFIG)"
dotnet build "$SLN" --configuration "$CONFIG" --nologo --verbosity minimal

BUILD_OUT="$SCRIPT_DIR/bin/$CONFIG/net8.0"
if [[ ! -f "$BUILD_OUT/rhinomcp.rhp" ]]; then
  echo "error: build succeeded but rhinomcp.rhp is not at $BUILD_OUT" >&2
  exit 1
fi

echo "==> installing to $RHINO_PLUGIN_DIR"
mkdir -p "$RHINO_PLUGIN_DIR"
# rsync --delete so stale dlls from a previous build / NuGet upgrade don't
# linger and shadow the freshly-built ones at load time.
rsync -a --delete "$BUILD_OUT/" "$RHINO_PLUGIN_DIR/"

echo
echo "done. Plugin staged at:"
echo "  $RHINO_PLUGIN_DIR/rhinomcp.rhp"
echo
if [[ -z "${RHINOMCP_REGISTERED:-}" ]]; then
  cat <<EOF
First-time install only:
  1. Launch Rhino 8.
  2. Drag the .rhp file (above) onto an open Rhino viewport.
  3. Accept the load dialog. Rhino now remembers the path and will pick up
     every subsequent rebuild on its next launch.

  After step 3, set RHINOMCP_REGISTERED=1 in your shell to silence this note:
    export RHINOMCP_REGISTERED=1

Once registered, run 'mcpstart' in the Rhino command line to start the TCP
listener on 127.0.0.1:1999, then point your MCP client at the Python server.
EOF
fi
