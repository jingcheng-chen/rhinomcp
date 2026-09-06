import base64
import json
import hashlib
import pytest
from experiments.saved_review_mcp import read_image
from experiments.saved_review import delivery


def pack(tmp_path, monkeypatch):
    data = b"png-fixture"
    (tmp_path / "one.png").write_bytes(data)
    images = {
        "candidate/front": {
            "file": "one.png",
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    }
    raw = json.dumps({"images": images}).encode()
    (tmp_path / "manifest.json").write_bytes(raw)
    monkeypatch.setenv("REVIEW_MANIFEST_SHA256", hashlib.sha256(raw).hexdigest())
    return data, images


@pytest.mark.parametrize(
    "fault", ["unknown", "changed_image", "changed_manifest", "symlink", "traversal"]
)
def test_frozen_pack_boundary(tmp_path, monkeypatch, fault):
    data, images = pack(tmp_path, monkeypatch)
    assert read_image(tmp_path, "candidate/front")[0] == data
    image_id = "candidate/front"
    if fault == "unknown":
        image_id = "held-out/back"
    elif fault == "changed_image":
        (tmp_path / "one.png").write_bytes(b"changed")
    elif fault == "changed_manifest":
        (tmp_path / "manifest.json").write_text("{}")
    elif fault == "symlink":
        (tmp_path / "one.png").unlink()
        (tmp_path / "one.png").symlink_to(tmp_path / "elsewhere.png")
    else:
        images[image_id]["file"] = "../outside.png"
        raw = json.dumps({"images": images}).encode()
        (tmp_path / "manifest.json").write_bytes(raw)
        monkeypatch.setenv("REVIEW_MANIFEST_SHA256", hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        read_image(tmp_path, image_id)


def test_delivery_requires_matching_client_image(tmp_path, monkeypatch):
    data, images = pack(tmp_path, monkeypatch)
    image_id = "candidate/front"
    (tmp_path / "delivered.jsonl").write_text(
        json.dumps({"image_id": image_id, "sha256": images[image_id]["sha256"]})
    )
    assert not delivery(tmp_path, images)["complete"]
    (tmp_path / "planner").mkdir()
    event = {
        "type": "item.completed",
        "item": {
            "type": "mcp_tool_call",
            "tool": "get_review_image",
            "status": "completed",
            "arguments": {"image_id": image_id},
            "result": {
                "content": [
                    {"type": "image", "data": base64.b64encode(b"wrong").decode()}
                ]
            },
        },
    }
    path = tmp_path / "planner/events.jsonl"
    path.write_text(json.dumps(event))
    assert not delivery(tmp_path, images)["complete"]
    event["item"]["result"]["content"][0]["data"] = base64.b64encode(data).decode()
    path.write_text(json.dumps(event))
    assert delivery(tmp_path, images)["complete"]
