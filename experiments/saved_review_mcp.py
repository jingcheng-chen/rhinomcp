"""Read-only, hash-pinned PNG gateway; does not connect to Rhino."""

import hashlib
import json
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("Saved model image review")
calls = 0


def read_image(pack, image_id):
    manifest_bytes = (pack / "manifest.json").read_bytes()
    if (
        hashlib.sha256(manifest_bytes).hexdigest()
        != os.environ["REVIEW_MANIFEST_SHA256"]
    ):
        raise ValueError("Review manifest changed")
    manifest = json.loads(manifest_bytes)
    if image_id not in manifest["images"]:
        raise ValueError("Unknown review image")
    entry = manifest["images"][image_id]
    filename = entry["file"]
    if Path(filename).name != filename or not filename.endswith(".png"):
        raise ValueError("Review image must be a PNG basename")
    path = pack / filename
    if path.is_symlink():
        raise ValueError("Review image cannot be a symlink")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry["sha256"]:
        raise ValueError("Review image changed")
    return data, digest


@mcp.tool(annotations={"readOnlyHint": True})
def get_review_image(image_id: str) -> Image:
    """Receive one saved reference or candidate PNG. Use only exact image IDs
    listed in the review prompt. No live Rhino operations or arbitrary file paths.
    """
    global calls
    calls += 1
    if calls > 14:
        raise RuntimeError("Review image budget exhausted")
    data, digest = read_image(Path(os.environ["REVIEW_PACK"]), image_id)
    with Path(os.environ["REVIEW_LOG"]).open("a") as stream:
        stream.write(json.dumps({"image_id": image_id, "sha256": digest}) + "\n")
    return Image(data=data, format="png")


if __name__ == "__main__":
    mcp.run()
