"""Live framing regression for a dedicated black-wireframe prism document.

Run with --model pointing to a saved passing prism and an empty active Rhino doc.
Pixel bounds are a fixture-specific capture check, never a geometry evaluator.
"""

import argparse
import base64
import json
import time
from pathlib import Path

from PIL import Image

from experiments.bridge import assert_document, identity, script
from experiments.runner import ROOT, save, sha256
from rhinomcp.server import get_rhino_connection


STATE = """
var views = new System.Collections.Generic.List<object>();
foreach (var view in doc.Views) {
    var p = view.ActiveViewport;
    p.GetFrustum(out double l, out double r, out double b, out double t,
                 out double n, out double f);
    views.Add(new { p.Id, p.Name, p.CameraLocation, p.CameraTarget,
        p.CameraDirection, p.CameraUp, p.IsPerspectiveProjection,
        p.IsParallelProjection, width=p.Size.Width, height=p.Size.Height,
        frustum=new[]{l,r,b,t,n,f}, displayMode=p.DisplayMode.Id });
}
output.AppendLine(Serialize(new { views, doc.Modified,
    active=doc.Views.ActiveView.ActiveViewportID,
    objects=doc.Objects.Where(o => o != null && !o.IsDeleted).Select(o => new {o.Id, crc=o.Geometry.DataCRC(0)}).ToArray()
}));
"""


def equivalent(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) <= 1e-8
    return a == b


def pixel_bounds(path):
    # Read the saved image in the controller, not a slow per-pixel Rhino script.
    # Preserve the original predicate exactly: R, G and B are each below 80.
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = rgb.load()
        left, right, top, bottom, count = width, -1, height, -1, 0
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if r < 80 and g < 80 and b < 80:
                    left, right = min(left, x), max(right, x)
                    top, bottom = min(top, y), max(bottom, y)
                    count += 1
    return dict(
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        count=count,
        width=width,
        height=height,
    )


def validate(model):
    model = model.resolve(strict=True)
    state = identity()
    if state["object_count"] or state["path"]:
        raise RuntimeError("Create a new empty unsaved Rhino document first")
    marker = "capture-validation-" + time.strftime("%Y%m%d-%H%M%S")
    directory = ROOT / "experiments/runs" / marker
    directory.mkdir(parents=True)
    script(f"""
doc.Strings.SetString("rhinomcp_experiment", {json.dumps(marker)});
using(var model=Rhino.FileIO.File3dm.Read({json.dumps(str(model))})) {{
    foreach(var obj in model.Objects) {{
        var attributes=obj.Attributes.Duplicate();
        attributes.ObjectColor=System.Drawing.Color.Black;
        attributes.ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject;
        doc.Objects.Add(obj.Geometry,attributes);
    }}
}}
foreach(var view in doc.Views)
    view.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.FindByName("Wireframe");
// Deliberately leave the new geometry display cache unrefreshed.
""")
    report = {"environment": identity(), "model_sha256": sha256(model), "cases": {}}
    # Back has no dedicated viewport in the standard four-view layout, exercising
    # temporary reprojection and name restoration as well as camera fitting.
    cases = [
        (v, w, h, True)
        for v in ("perspective", "top", "back")
        for w, h in ((1000, 750), (400, 1000), (1000, 400))
    ]
    cases.append(("perspective", 1000, 750, False))
    for view, width, height, fit in cases:
        assert_document(state["document"], marker)
        name = f"{view}-{width}-{height}-fit-{fit}"
        before = json.loads(script(STATE))
        result = get_rhino_connection().send_command(
            "capture_viewport",
            {
                "viewport": view,
                "width": width,
                "height": height,
                "zoom_to_fit": fit,
                "show_grid": False,
                "show_axes": False,
                "show_cplane_axes": False,
            },
        )
        after = json.loads(script(STATE))
        path = directory / f"{name}.png"
        path.write_bytes(base64.b64decode(result["image_data"]))
        bounds = pixel_bounds(path)
        framed = (
            bounds["count"] > 500
            and bounds["left"] >= 5
            and bounds["top"] >= 5
            and bounds["right"] < width - 5
            and bounds["bottom"] < height - 5
        )
        case = {
            "before": before,
            "after": after,
            "pixels": bounds,
            "state_preserved": equivalent(before, after),
            "dimensions_correct": (bounds["width"], bounds["height"])
            == (width, height),
            "framing_required": fit,
            "framed": framed,
        }
        case["passed"] = (
            case["state_preserved"]
            and case["dimensions_correct"]
            and (not fit or framed)
        )
        report["cases"][name] = case
    before = json.loads(script(STATE))
    rejected = False
    try:
        get_rhino_connection().send_command(
            "capture_viewport", {"viewport": "missing-capture-test-view"}
        )
    except Exception:
        rejected = True
    after = json.loads(script(STATE))
    report["cases"]["invalid-view"] = {"passed": rejected and equivalent(before, after)}
    report["passed"] = all(c["passed"] for c in report["cases"].values())
    save(directory / "validation.json", report)
    print(directory)
    print(json.dumps({k: v["passed"] for k, v in report["cases"].items()}, indent=2))
    return report["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if validate(args.model) else 1)
