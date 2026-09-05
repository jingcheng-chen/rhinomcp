"""Trusted generation of calibrated box drawings from a saved reference model."""

import json
from pathlib import Path

from experiments.bridge import script

VIEWS = {"top": (0, 1, "X", "Y"), "front": (0, 2, "X", "Z"), "right": (1, 2, "Y", "Z")}


def generate(task, directory):
    # Import here to avoid a runner/references module cycle.
    from experiments.runner import save, sha256

    directory.mkdir()
    (directory / "generator.py").write_bytes(Path(__file__).read_bytes())
    model = directory / "reference.3dm"
    x, y, z = task["dimensions"]
    script(f"""
using(var model = new Rhino.FileIO.File3dm()) {{
    model.Settings.ModelUnitSystem = UnitSystem.Millimeters;
    var box = new Box(Plane.WorldXY, new Interval(0,{x}), new Interval(0,{y}), new Interval(0,{z}));
    model.Objects.AddBrep(box.ToBrep(), new Rhino.DocObjects.ObjectAttributes());
    if(!model.Write({json.dumps(str(model))},8)) throw new Exception("Reference save failed");
}}
""")
    public = {
        "grid_mm": 10,
        "pixels_per_mm": 5,
        "origin_pixel": [100, 500],
        "views": {},
    }
    for name, (horizontal, vertical, hlabel, vlabel) in VIEWS.items():
        path = directory / f"{name}.png"
        script(f"""
using(var model = Rhino.FileIO.File3dm.Read({json.dumps(str(model))})) {{
    var bounds = BoundingBox.Empty;
    foreach(var obj in model.Objects) bounds.Union(obj.Geometry.GetBoundingBox(true));
    var size = new[] {{bounds.Max.X, bounds.Max.Y, bounds.Max.Z}};
    using(var bitmap = new System.Drawing.Bitmap(700,600))
    using(var g = System.Drawing.Graphics.FromImage(bitmap))
    using(var font = new System.Drawing.Font("Arial",12))
    using(var outline = new System.Drawing.Pen(System.Drawing.Color.Black,2)) {{
        g.Clear(System.Drawing.Color.White);
        g.DrawString("{name.upper()} — orthographic; grid = 10 mm",font,System.Drawing.Brushes.Black,70,25);
        for(int i=0;i<=10;i++) {{
            int px=100+50*i;
            g.DrawLine(System.Drawing.Pens.LightGray,px,100,px,500);
            g.DrawString((i*10).ToString(),font,System.Drawing.Brushes.Black,px-8,510);
        }}
        for(int i=0;i<=8;i++) {{
            int py=500-50*i;
            g.DrawLine(System.Drawing.Pens.LightGray,100,py,600,py);
            g.DrawString((i*10).ToString(),font,System.Drawing.Brushes.Black,65,py-8);
        }}
        g.DrawLine(System.Drawing.Pens.Black,100,500,620,500);
        g.DrawLine(System.Drawing.Pens.Black,100,500,100,80);
        g.DrawString("+{hlabel} (mm)",font,System.Drawing.Brushes.Black,545,545);
        g.DrawString("+{vlabel}",font,System.Drawing.Brushes.Black,100,65);
        g.DrawRectangle(outline,100f,(float)(500-5*size[{vertical}]),
            (float)(5*size[{horizontal}]),(float)(5*size[{vertical}]));
        bitmap.Save({json.dumps(str(path))},System.Drawing.Imaging.ImageFormat.Png);
    }}
}}
""")
        public["views"][name] = {
            "horizontal_axis": hlabel,
            "vertical_axis": vlabel,
            "projection": "orthographic",
            "sha256": sha256(path),
        }
    save(directory / "views.json", public)
    return {
        "model_sha256": sha256(model),
        "generator_sha256": sha256(directory / "generator.py"),
        "public": public,
    }


def reference_image(view):
    """Only fixed public PNGs are exposed; the saved reference model stays private."""
    import os
    from mcp.server.fastmcp import Image
    from experiments.runner import sha256

    if view not in VIEWS:
        raise ValueError("Unknown reference view")
    directory = Path(os.environ["EXPERIMENT_REFERENCE_DIR"])
    manifest = json.loads((directory / "views.json").read_text())
    path = directory / f"{view}.png"
    if sha256(path) != manifest["views"][view]["sha256"]:
        raise RuntimeError("Reference image changed")
    return Image(data=path.read_bytes(), format="png")
