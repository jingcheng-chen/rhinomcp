import copy
from uuid import uuid4
import pytest
from experiments.integration_audit import evaluate, PATHS
from experiments.layer_probe import ZERO


def fixture():
    paths = sorted(PATHS)
    index = {p: i for i, p in enumerate(paths)}
    layers = [
        dict(
            id=str(i),
            index=i,
            name=p.split("::")[-1],
            parent=str(index[p.rsplit("::", 1)[0]]) if "::" in p else ZERO,
            visible=True,
            locked=False,
        )
        for i, p in enumerate(paths)
    ]
    objects = [
        dict(
            name=name,
            layer=index[layer],
            visible=True,
            mode="Normal",
            valid=True,
            solid=True,
            nonplanar=1,
            naked=0,
        )
        for name, layer in [
            ("seat_body", "Chair::Upholstery::Seat"),
            ("back_body", "Chair::Upholstery::Back"),
            ("frame_left", "Chair::Frame::Left"),
            ("straps_seat", "Chair::Straps"),
        ]
    ]
    return dict(layers=layers, objects=objects)


@pytest.mark.parametrize("fault", ["layer", "open", "planar", "hidden", "missing"])
def test_observations_detect_regressions(fault):
    data = fixture()
    assert all(evaluate(data)["checks"].values())
    data = copy.deepcopy(data)
    if fault == "layer":
        data["objects"][0]["layer"] = 0
    elif fault == "open":
        data["objects"][2]["solid"] = False
    elif fault == "planar":
        data["objects"][1]["nonplanar"] = 0
    elif fault == "hidden":
        data["layers"][0]["visible"] = False
    elif fault == "missing":
        data["objects"].pop(0)
    result = evaluate(data)
    assert not all(result["checks"].values())
    assert result["visual_acceptance"] == "unscored"


def test_review_cannot_join(monkeypatch):
    from experiments import integration_mcp as module

    monkeypatch.setattr(module.visual, "guard", lambda: None)
    monkeypatch.setenv("EXPERIMENT_READ_ONLY", "1")
    monkeypatch.setattr(
        module, "get_rhino_connection", lambda: pytest.fail("No mutation allowed")
    )
    with pytest.raises(RuntimeError, match="Review"):
        module.join_surfaces([str(uuid4()), str(uuid4())])


def test_review_requires_all_image_deliveries(tmp_path):
    import json
    from experiments.integration_audit import review_evidence

    (tmp_path / "references").mkdir()
    (tmp_path / "references/public.json").write_text(
        json.dumps({"views": {"front": {}}})
    )
    assert not review_evidence(tmp_path)["image_delivery_complete"]
    log = tmp_path / "review-tools.jsonl"
    events = [{"reference_view": "front"}, {"candidate_view": "perspective"}]
    log.write_text("\n".join(map(json.dumps, events)))
    assert review_evidence(tmp_path)["missing_candidate_views"] == ["back", "right"]
    events += [{"candidate_view": v} for v in ["right", "back"]]
    log.write_text("\n".join(map(json.dumps, events)))
    assert review_evidence(tmp_path)["image_delivery_complete"]
