"""Fresh image review of an explicit saved pack, with server and client evidence."""

import json
import base64
import hashlib
import sys
import time
import uuid
from pathlib import Path
from experiments.runner import ROOT, save, sha256, run_session, PLANNER_SCHEMA


def delivery(directory, images):
    path = directory / "delivered.jsonl"
    sent = (
        [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    )
    events = directory / "planner/events.jsonl"
    received = []
    if events.exists():
        for line in events.read_text().splitlines():
            event = json.loads(line)
            item = event.get("item", {})
            if (
                event.get("type") == "item.completed"
                and item.get("type") == "mcp_tool_call"
                and item.get("tool") == "get_review_image"
                and item.get("status") == "completed"
                and not item.get("error")
            ):
                image_id = item.get("arguments", {}).get("image_id")
                result = item.get("result") or {}
                if image_id in images and not result.get("isError"):
                    for content in result.get("content", []):
                        if content.get("type") != "image":
                            continue
                        try:
                            digest = hashlib.sha256(
                                base64.b64decode(content.get("data", ""), validate=True)
                            ).hexdigest()
                        except ValueError:
                            continue
                        if digest == images[image_id]["sha256"]:
                            received.append(image_id)
    server_ids = {
        s["image_id"]
        for s in sent
        if s.get("image_id") in images
        and s.get("sha256") == images[s["image_id"]]["sha256"]
    }
    missing = sorted(set(images) - (server_ids & set(received)))
    return {
        "complete": not missing,
        "missing": missing,
        "server_ids": sorted(server_ids),
        "client_ids": sorted(set(received)),
        "limitation": "Successful image calls establish delivery, not calibrated visual judgment.",
    }


def run(sources, context):
    directory = (
        ROOT
        / "experiments/runs"
        / (time.strftime("saved-review-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    )
    directory.mkdir()
    print(directory, flush=True)
    pack = directory / "pack"
    pack.mkdir()
    images = {}
    source_hashes = {str(p): sha256(p) for p in sources.values()}
    for index, (image_id, path) in enumerate(sources.items()):
        filename = f"image-{index}.png"
        (pack / filename).write_bytes(path.read_bytes())
        images[image_id] = {"file": filename, "sha256": sha256(pack / filename)}
    save(pack / "manifest.json", {"images": images})
    save(directory / "sources.json", source_hashes)
    names = [
        "experiments/saved_review.py",
        "experiments/saved_review_mcp.py",
        "experiments/runner.py",
    ]
    pins = {name: sha256(ROOT / name) for name in names}
    save(directory / "inputs.json", pins)
    for name in names:
        out = directory / "source" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((ROOT / name).read_bytes())
    env = {
        "PYTHONPATH": str(ROOT),
        "REVIEW_PACK": str(pack),
        "REVIEW_MANIFEST_SHA256": sha256(pack / "manifest.json"),
        "REVIEW_LOG": str(directory / "delivered.jsonl"),
    }
    config = {
        "command": json.dumps(sys.executable),
        "args": json.dumps(["-m", "experiments.saved_review_mcp"]),
        "cwd": json.dumps(str(ROOT)),
        "required": "true",
        "env": "{ "
        + ", ".join(f"{k} = {json.dumps(v)}" for k, v in env.items())
        + " }",
        "tools.get_review_image.approval_mode": '"approve"',
    }
    prompt = (
        "You are an independent diagnostic planner. First call the rhino_experiment MCP tool get_review_image(image_id) for EVERY ID below. These tools return actual images; do not guess paths or query MCP resources. If unavailable, explicitly report incomplete review and do not infer visual details. Compare visible shapes and separate observations from measurement evidence and guesses. Images are not camera-calibrated; visual acceptance stays unscored. Recommend one small transferable experiment; do not invent a plugin defect. Image IDs: "
        + json.dumps(list(images))
        + "\nContext: "
        + json.dumps(context)
    )
    result = run_session(directory / "planner", prompt, PLANNER_SCHEMA, 240, config)
    evidence = delivery(directory, images)
    unchanged = source_hashes == {
        str(p): sha256(p) for p in sources.values()
    } and pins == {name: sha256(ROOT / name) for name in names}
    unchanged = (
        unchanged
        and sha256(pack / "manifest.json") == env["REVIEW_MANIFEST_SHA256"]
        and all(sha256(pack / e["file"]) == e["sha256"] for e in images.values())
    )
    save(
        directory / "summary.json",
        {
            "planner": result,
            "delivery": evidence,
            "inputs_preserved": unchanged,
            "status": "reviewed_unscored"
            if evidence["complete"] and unchanged
            else "incomplete_review",
        },
    )
    if not unchanged:
        raise RuntimeError("Review input changed")
    return directory


def chair_sources(directory):
    refs = directory / "references"
    manifest = json.loads((refs / "public.json").read_text())
    sources = {
        "reference/" + view: refs / meta["file"]
        for view, meta in manifest["views"].items()
    }
    sources.update(
        {
            "candidate/" + view: directory / "comparison" / f"candidate-{view}.png"
            for view in ["perspective", "front", "right"]
        }
    )
    return sources


if __name__ == "__main__":
    directory = Path(sys.argv[1]).resolve()
    summary = json.loads((directory / "summary.json").read_text())
    run(
        chair_sources(directory),
        {
            "measurements": summary["structural_checks"],
            "integration": summary["integration"]["checks"],
            "known_geometry": "Back cushion is valid but open with four naked edges; seat and frame are solids. 28 objects, width 1000 mm. Neither image similarity nor this closure failure establishes a plugin defect.",
            "preserve": "61-case production contract; original chair and current saved candidate.",
        },
    )
