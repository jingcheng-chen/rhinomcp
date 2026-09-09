"""Supervisor-only shaded progress capture; restore each viewport's display mode."""

import base64
import json

from rhinomcp.server import get_rhino_connection
from experiments.bridge import script, assert_document
from experiments.runner import sha256, save


def capture_shaded(directory, serial, marker):
    assert_document(serial, marker)
    modes = json.loads(
        script("""
output.AppendLine(Serialize(doc.Views.Select(v=>new {id=v.ActiveViewport.Id,mode=v.ActiveViewport.DisplayMode.Id}).ToArray()));
""")
    )
    save(directory / "display-modes-before.json", modes)
    try:
        script("""
foreach(var view in doc.Views) view.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.ShadedId);
doc.Views.Redraw();
""")
        images = {}
        for view in ("perspective", "top", "front"):
            assert_document(serial, marker)
            result = get_rhino_connection().send_command(
                "capture_viewport",
                {
                    "viewport": view,
                    "width": 1000,
                    "height": 750,
                    "show_grid": False,
                    "show_axes": False,
                    "show_cplane_axes": False,
                    "zoom_to_fit": True,
                },
            )
            path = directory / (view + "-shaded.png")
            path.write_bytes(base64.b64decode(result["image_data"]))
            images[view] = {"file": path.name, "sha256": sha256(path)}
        save(
            directory / "screenshots.json",
            {
                "kind": "actual_rhino_capture",
                "display": "Shaded",
                "views": images,
                "visual_acceptance": "unscored",
            },
        )
    finally:
        assert_document(serial, marker)
        for item in modes:
            script(
                f"""var view=doc.Views.FirstOrDefault(v=>v.ActiveViewport.Id==new Guid({json.dumps(item["id"])})); if(view==null) throw new Exception("Capture viewport disappeared"); view.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(new Guid({json.dumps(item["mode"])}));"""
            )
        script("doc.Views.Redraw();")
        after = json.loads(
            script(
                "output.AppendLine(Serialize(doc.Views.Select(v=>new {id=v.ActiveViewport.Id,mode=v.ActiveViewport.DisplayMode.Id}).ToArray()));"
            )
        )
        save(
            directory / "display-modes-restored.json",
            {"modes": after, "restored": after == modes},
        )
        if after != modes:
            raise RuntimeError("Viewport display modes changed")
