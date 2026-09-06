"""Calibrate the posed-strip task judge with independently extruded sectors."""

import json
from pathlib import Path

from experiments.bridge import script, assert_document
from experiments.runner import ROOT, save, sha256, load_task
from experiments.strip_probe import fingerprint
from experiments.strip_task import measure, evaluate


def validate(directory, owner):
    directory = Path(directory)
    directory.mkdir()
    before = fingerprint()
    assert_document(owner["document"], owner["marker"])
    origin = load_task(ROOT / "experiments/tasks/quarter_strip_origin.json")
    posed = load_task(ROOT / "experiments/tasks/quarter_strip_translated.json")
    source = ROOT / "experiments/strip_controls.cs"
    (directory / source.name).write_bytes(source.read_bytes())
    script(source.read_text().replace("OUTPUT_DIRECTORY", json.dumps(str(directory))))
    source_path = directory / "independent_correct.3dm"
    posed_path = directory / "translated_correct.3dm"
    x, y, z = posed["translation"]
    script(f"""
using(var f=Rhino.FileIO.File3dm.Read({json.dumps(str(source_path))})) {{
 using(var result=new Rhino.FileIO.File3dm()) {{
  result.Settings.ModelUnitSystem=f.Settings.ModelUnitSystem;
  foreach(var obj in f.Objects) {{
   var geometry=obj.Geometry.Duplicate();
   geometry.Transform(Transform.Translation({x},{y},{z}));
   result.Objects.Add(geometry,obj.Attributes);
  }}
  if(!result.Write({json.dumps(str(posed_path))},8)) throw new Exception("Fixture write failed");
 }}
}}
""")
    reports = {}
    cases = [
        (name, origin, name.startswith("independent"))
        for name in [
            "independent_correct",
            "independent_outward",
            "wrong_width",
            "equal_volume_wrong_radius",
            "wrong_position",
            "extra_object",
        ]
    ]
    cases += [
        ("translated_correct", posed, True),
        ("translated_correct", origin, False),
        ("independent_correct", posed, False),
    ]
    for name, task, expected in cases:
        path = directory / (name + ".3dm")
        a, b = measure(path, task), measure(path, task)
        report = evaluate(task, a)
        report.update(
            repeat_identical=a == b, artifact_sha256=sha256(path), expected=expected
        )
        reports[name + "/" + task["id"]] = report
        if (report["status"] == "pass") != expected or a != b:
            save(directory / "validation.json", reports)
            raise RuntimeError("Unexpected strip calibration verdict")
    assert_document(owner["document"], owner["marker"])
    if fingerprint() != before:
        raise RuntimeError("Calibration altered the active document")
    save(directory / "validation.json", reports)
    return reports
