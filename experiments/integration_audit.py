"""Saved-file integration observations; never a visual acceptance score."""

import json
from experiments.bridge import script
from experiments.runner import ROOT, sha256
from experiments.layer_probe import ZERO

PATHS = {
    "Chair",
    "Chair::Frame",
    "Chair::Frame::Left",
    "Chair::Frame::Right",
    "Chair::Upholstery",
    "Chair::Upholstery::Seat",
    "Chair::Upholstery::Back",
    "Chair::Straps",
}


def evaluate(data):
    by_id = {layer["id"]: layer for layer in data["layers"]}

    def path(layer, seen=()):
        if layer["id"] in seen:
            raise ValueError("Cycle")
        return (
            layer["name"]
            if layer["parent"] == ZERO
            else path(by_id[layer["parent"]], (*seen, layer["id"]))
            + "::"
            + layer["name"]
        )

    try:
        paths = {layer["index"]: path(layer) for layer in data["layers"]}
    except (KeyError, ValueError):
        paths = {}
    chair = {p for p in paths.values() if p == "Chair" or p.startswith("Chair::")}
    checks = {
        "layer_tree": chair == PATHS,
        "visible_unlocked": bool(data["objects"])
        and all(o["visible"] and o["mode"] == "Normal" for o in data["objects"])
        and all(
            layer["visible"] and not layer["locked"]
            for layer in data["layers"]
            if paths.get(layer["index"]) in PATHS
        ),
    }
    for prefix, leaf in [("seat", "Seat"), ("back", "Back")]:
        matches = [o for o in data["objects"] if o["name"] == prefix + "_body"]
        checks[prefix + "_body"] = (
            len(matches) == 1
            and matches[0]["solid"]
            and matches[0]["valid"]
            and matches[0]["naked"] == 0
            and matches[0]["nonplanar"] >= 1
            and paths.get(matches[0]["layer"]) == "Chair::Upholstery::" + leaf
        )
    frame = [o for o in data["objects"] if o["name"].startswith("frame_")]
    checks["closed_frame"] = bool(frame) and all(
        o["valid"] and o["solid"] and o["naked"] == 0 for o in frame
    )

    def assigned(o):
        p = paths.get(o["layer"], "")
        if o["name"].startswith("frame_"):
            return p in {"Chair::Frame", "Chair::Frame::Left", "Chair::Frame::Right"}
        if o["name"].startswith("seat_"):
            return p == "Chair::Upholstery::Seat"
        if o["name"].startswith("back_"):
            return p == "Chair::Upholstery::Back"
        if o["name"].startswith("straps_"):
            return p == "Chair::Straps"
        return False

    checks["assignments"] = bool(data["objects"]) and all(
        assigned(o) for o in data["objects"]
    )
    return {
        "checks": checks,
        "measurements": data,
        "visual_acceptance": "unscored",
        "limitation": "Names do not establish semantics; a nonplanar solid is not proof of correct cushion shape or continuous tufting.",
    }


def audit(path):
    before = sha256(path)
    code = (
        (ROOT / "experiments/integration_audit.cs")
        .read_text()
        .replace("ARTIFACT_PATH", json.dumps(str(path)))
    )
    a, b = json.loads(script(code)), json.loads(script(code))
    if a != b or sha256(path) != before:
        raise RuntimeError("Audit changed")
    return {**evaluate(a), "repeat_identical": True}


def review_evidence(directory):
    """Tool delivery is necessary evidence of image review, not proof of understanding."""
    manifest = json.loads((directory / "references/public.json").read_text())
    path = directory / "review-tools.jsonl"
    events = (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )
    refs = {event["reference_view"] for event in events if "reference_view" in event}
    views = {event["candidate_view"] for event in events if "candidate_view" in event}
    missing_refs = sorted(set(manifest["views"]) - refs)
    missing_views = sorted({"perspective", "right", "back"} - views)
    return {
        "image_delivery_complete": not missing_refs and not missing_views,
        "missing_references": missing_refs,
        "missing_candidate_views": missing_views,
        "limitation": "Tool logs establish image delivery only. Missing delivery leaves the planner's visual claims unsupported; visual acceptance remains unscored.",
    }
