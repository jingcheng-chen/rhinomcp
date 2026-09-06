from uuid import uuid4
import copy

import pytest

from experiments.cushion_body_mcp import join_script
from experiments.cushion_body_probe import evaluate, samples, scale_value
from experiments.cushion_probe import height
from experiments.layer_probe import ZERO


@pytest.mark.parametrize(
    "ids",
    [
        [],
        ["x", "y"],
        [str(uuid4()), "_Enter _Delete"],
        ["00000000-0000-0000-0000-000000000000", str(uuid4())],
    ],
)
def test_join_rejects_invalid_or_injected_ids(ids):
    with pytest.raises(ValueError):
        join_script(ids)


def test_join_is_fixed_and_deduplicated():
    a, b = str(uuid4()), str(uuid4())
    assert (
        join_script([a, b]) == f"_SelNone _SelID {a} _SelID {b} _Join _Enter _SelNone"
    )
    with pytest.raises(ValueError):
        join_script([a, a])


def correct(scale=1):
    return dict(
        units="Millimeters",
        layers=[
            dict(
                id=str(i),
                index=i,
                parent=str(i - 1) if i else ZERO,
                name=name,
                visible=True,
                locked=False,
            )
            for i, name in enumerate(["Cushion", "Upholstery", "Body"])
        ],
        objects=[
            dict(
                name="cushion_body",
                layer=2,
                visible=True,
                mode="Normal",
                valid=True,
                faces=6,
                solid=True,
                nonplanar=1,
                untrimmed=True,
                smooth=True,
                min=[0, 0, 0],
                max=[100 * scale, 100 * scale, 30 * scale],
                points=[
                    [i * 2.5 * scale, j * 2.5 * scale, height(i * 2.5, j * 2.5) * scale]
                    for i in range(41)
                    for j in range(41)
                ],
                distances=[0] * 441,
                naked_edges=0,
                boundaryPlanes=True,
                hasBottom=True,
                volume=10000 * (10 + 20 * (18 / 35) ** 2) * scale**3,
                membership=[
                    0 < x < 100 and 0 < y < 100 and 0 < z < height(x, y)
                    for x, y, z in samples()
                ],
            )
        ],
    )


def test_scaled_body_and_cross_evaluation():
    assert evaluate(correct(0.75), 0.75)["status"] == "pass"
    assert evaluate(correct(0.75), 1)["status"] == "fail"
    with pytest.raises(ValueError):
        scale_value(0)


@pytest.mark.parametrize(
    "fault", ["open", "naked", "bottom", "volume", "membership", "layer", "flat"]
)
def test_body_faults_fail(fault):
    data = correct()
    assert evaluate(data)["status"] == "pass"
    data = copy.deepcopy(data)
    obj = data["objects"][0]
    if fault == "open":
        obj["solid"] = False
    elif fault == "naked":
        obj["naked_edges"] = 1
    elif fault == "bottom":
        obj["hasBottom"] = False
    elif fault == "volume":
        obj["volume"] *= 0.8
    elif fault == "membership":
        obj["membership"][0] = not obj["membership"][0]
    elif fault == "layer":
        data["layers"][-1]["name"] = "Top"
    elif fault == "flat":
        for p in obj["points"]:
            p[2] = 10
    assert evaluate(data)["status"] == "fail"
