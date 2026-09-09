"""Measure warmed accurate-bounds versus deep-copy bounds on saved Breps.

This is an operation microbenchmark, not an agent-efficiency comparison. Input
geometry is read from files without insertion into the active Rhino document.
"""

import argparse
import json
from pathlib import Path
import statistics
import time

from experiments.bridge import script
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run(paths):
    directory = ROOT / "experiments/runs" / time.strftime("bounds-cost-%Y%m%d-%H%M%S")
    directory.mkdir()
    inputs = [{"path": str(p.resolve(strict=True)), "sha256": sha256(p)} for p in paths]
    results = []
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        for item in inputs:
            code = r"""
using(var file=Rhino.FileIO.File3dm.Read(INPUT)) {
var records=new System.Collections.Generic.List<object>();
foreach(var obj in file.Objects) {
var b=obj.Geometry as Brep;
if(b==null) continue;
var crc=b.DataCRC(0);
var expected=b.GetBoundingBox(true);
using(var copy=b.DuplicateBrep()) {
var check=copy.GetBoundingBox(true);
if(check.Min.DistanceTo(expected.Min)>1e-6 || check.Max.DistanceTo(expected.Max)>1e-6)
throw new Exception("Bounds disagree; do not compare speed of different results");
}
var direct=new System.Collections.Generic.List<double>();
var copied=new System.Collections.Generic.List<double>();
double sink=0;
for(int block=0;block<10;block++) {
for(int order=0;order<2;order++) {
bool duplicate=(block+order)%2==1;
var watch=System.Diagnostics.Stopwatch.StartNew();
for(int i=0;i<100;i++) {
if(duplicate) {using(var copy=b.DuplicateBrep()) {sink+=copy.GetBoundingBox(true).Max.Z;}}
else {sink+=b.GetBoundingBox(true).Max.Z;}
}
watch.Stop();
(duplicate?copied:direct).Add(watch.Elapsed.TotalMilliseconds/100);
}
}
if(crc!=b.DataCRC(0))throw new Exception("Source geometry changed");
records.Add(new {faces=b.Faces.Count,direct_ms=direct,copy_ms=copied,source_unchanged=true,sink=sink});
}
if(records.Count==0)throw new Exception("Input contains no Breps");
output.AppendLine(Serialize(records));
}
""".replace("INPUT", json.dumps(item["path"]))
            (directory / f"measure-{len(results)}.cs").write_text(code)
            measured = json.loads(script(code))
            for record in measured:
                record["direct_median_ms"] = statistics.median(record["direct_ms"])
                record["copy_median_ms"] = statistics.median(record["copy_ms"])
            if sha256(Path(item["path"])) != item["sha256"]:
                raise RuntimeError("Input file changed during measurement")
            results.append({**item, "measurements": measured})
        require_owned(runtime(), owner)
        if fingerprint() != before:
            raise RuntimeError("Document state changed")
    save(
        directory / "results.json",
        {"runtime": owner, "inputs": results, "preserved": True},
    )
    (directory / "source.py").write_bytes(Path(__file__).read_bytes())
    print(directory)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path, nargs="+")
    run(parser.parse_args().models)
