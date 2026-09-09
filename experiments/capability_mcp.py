"""Exact-path source gateway for explicitly declared new commands."""

import os
from pathlib import Path
from threading import Lock

from mcp.server.mcpserver import MCPServer
from experiments.capability import load_manifest
from experiments.runner import sha256

mcp = MCPServer("RhinoMCP capability builder")
source_lock = Lock()
calls = 0


def checked_path(name, operation):
    global calls
    calls += 1
    if calls > 48:
        raise RuntimeError("Capability builder call budget exhausted")
    manifest = load_manifest(
        Path(os.environ["BUILDER_MANIFEST"]), os.environ["BUILDER_MANIFEST_SHA256"]
    )
    key = {"read": "read_paths", "replace": "write_paths", "create": "create_paths"}[
        operation
    ]
    # After creation the builder may read and revise the same declared file.
    allowed = manifest[key] + (
        manifest["create_paths"] if operation == "replace" else []
    )
    if name not in allowed:
        raise ValueError("Path is outside declared capability scope")
    root = Path(manifest["candidate"])
    target = root / name
    if any(
        p.is_symlink() for p in (target, *target.parents)
    ) or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe capability path")
    if operation == "create":
        if target.exists():
            raise ValueError("Creation target already exists")
    elif not target.is_file():
        raise ValueError("Source does not exist")
    return target


def content_bytes(content):
    data = content.encode("utf-8")
    if len(data) > 100000 or "\0" in content:
        raise ValueError("Source exceeds content limits")
    return data


@mcp.tool()
def read_source(path: str):
    """Read one approved source; hidden evaluators and unrestricted files are unavailable."""
    with source_lock:
        target = checked_path(path, "read")
        return {"path": path, "content": target.read_text(), "sha256": sha256(target)}


@mcp.tool()
def replace_source(path: str, expected_sha256: str, content: str):
    """Replace a declared source only if its previously read hash still matches."""
    with source_lock:
        target = checked_path(path, "replace")
        if sha256(target) != expected_sha256:
            raise ValueError("Source changed since read")
        target.write_bytes(content_bytes(content))
        return {"path": path, "sha256": sha256(target)}


@mcp.tool()
def create_source(path: str, content: str):
    """Create exactly one declared new file; never overwrite an existing file."""
    with source_lock:
        target = checked_path(path, "create")
        data = content_bytes(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        target.chmod(0o644)
        return {"path": path, "sha256": sha256(target)}


if __name__ == "__main__":
    mcp.run()
