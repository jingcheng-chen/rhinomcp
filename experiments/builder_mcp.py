"""Builder file gateway: exact paths, compare-before-write, no execution tools."""

import hashlib
import json
import os
from pathlib import Path
from threading import Lock

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("RhinoMCP bounded builder")
calls = 0
source_lock = Lock()


def checked_path(name, write=False):
    global calls
    calls += 1
    if calls > 24:
        raise RuntimeError("Builder call budget exhausted")
    data = Path(os.environ["BUILDER_MANIFEST"]).read_bytes()
    expected = os.environ.get("BUILDER_MANIFEST_SHA256")
    if expected is not None and digest(data) != expected:
        raise ValueError("Builder scope manifest changed")
    manifest = json.loads(data)
    allowed = manifest["write_paths" if write else "read_paths"]
    if name not in allowed:
        raise ValueError("Path is outside the builder scope")
    root = Path(manifest["candidate"])
    path = root / name
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("Symlinks are not allowed")
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Source file is outside the candidate")
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


@mcp.tool()
def read_source(path: str):
    """Read an explicitly allowed candidate source file and its SHA-256."""
    with source_lock:
        data = checked_path(path).read_bytes()
        return {"path": path, "sha256": digest(data), "content": data.decode("utf-8")}


@mcp.tool()
def replace_source(path: str, expected_sha256: str, content: str):
    """Replace an allowed source file only if it still matches the last read hash.

    No shell, build, installation, evaluator access, file creation or arbitrary paths.
    """
    with source_lock:
        target = checked_path(path, write=True)
        data = content.encode("utf-8")
        if len(data) > 50000 or "\0" in content:
            raise ValueError("Replacement exceeds source limits")
        if digest(target.read_bytes()) != expected_sha256:
            raise ValueError("Source changed since it was read")
        target.write_bytes(data)
        return {"path": path, "sha256": digest(data)}


if __name__ == "__main__":
    mcp.run()
