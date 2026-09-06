"""Live Rhino trial adapter with supervised desktop lifecycle handoffs.

No machine-specific plugin installation path is encoded here. The supervising
operator services a hash-bound lifecycle ticket through local installation rules.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from rhinomcp.server import get_rhino_connection

from experiments.bridge import identity, script, assert_document
from experiments.evaluator import evaluate
from experiments.runner import ROOT, load_task, measure, run_locked, save, sha256
from experiments.trial import persist, read, locked
from experiments.validate_capture import validate as capture_validate
from experiments.validate_live import validate_box, validate_prism
from experiments.validate_hole import validate_hole


def runtime():
    state = identity()
    extra = json.loads(
        script("""
output.AppendLine(Serialize(new {
 pid=System.Diagnostics.Process.GetCurrentProcess().Id,
 docs=Rhino.RhinoDoc.OpenDocuments().Select(d=>new {
 serial=d.RuntimeSerialNumber,path=d.Path,count=d.Objects.Count(o => o != null && !o.IsDeleted),modified=d.Modified
 }).ToArray()
}));
""")
    )
    return {**state, **extra}


def require_owned(state, owner):
    if state["pid"] != owner["pid"] or state["document"] != owner["document"]:
        raise RuntimeError("Rhino process/document is not owned by this trial")
    if len(state["docs"]) != 1 or state["path"]:
        raise RuntimeError("Trial requires one dedicated unsaved Rhino document")


def claim_empty(directory):
    state = runtime()
    if (
        len(state["docs"]) != 1
        or state["object_count"]
        or state["path"]
        or state["docs"][0]["modified"]
    ):
        raise RuntimeError("A single fresh empty unsaved Rhino document is required")
    owner = {"pid": state["pid"], "document": state["document"]}
    persist(directory / "runtime-owner.json", owner)
    return state


def probe(directory):
    state = runtime()
    require_owned(state, read(directory / "runtime-owner.json"))
    return {"sha256": sha256(Path(state["assembly"])), "mvid": state["mvid"]}


def clear_owned(directory, marker):
    state = runtime()
    require_owned(state, read(directory / "runtime-owner.json"))
    assert_document(state["document"], marker)
    script("""
foreach(var obj in doc.Objects.Where(o => o != null && !o.IsDeleted).ToArray()) doc.Objects.Delete(obj.Id,true);
doc.Strings.Delete("rhinomcp_experiment");
doc.Modified=false;
doc.Views.Redraw();
""")
    if identity()["object_count"]:
        raise RuntimeError("Trial document cleanup failed")


def lifecycle(request, request_path):
    directory = Path(request["trial"])
    owner = read(directory / "runtime-owner.json")
    try:
        before = runtime()
    except Exception as error:
        if request["action"] != "restore":
            raise
        # A stopped Rhino cannot answer a probe. Request supervised recovery;
        # the ticket is not permission to close an unrelated replacement process.
        before = {**owner, "unavailable": str(error)}
    else:
        require_owned(before, owner)
        if before["object_count"] or before.get("marker") is not None:
            raise RuntimeError(
                "Refuse restart while the dedicated document contains work"
            )
        # This process survives the desktop restart. Drop its old socket before
        # waiting, so post-restart identity cannot use a dead connection.
        get_rhino_connection().disconnect()
    key = "candidate_binary" if request["action"] == "install" else "baseline_binary"
    ticket = {
        "request_sha256": sha256(request_path),
        "action": request["action"],
        "binary": request[key],
        "expected_identity": request["expected_identity"],
        "previous_runtime": before,
        "instruction": "Supervisor: verify dedicated runtime, quit via desktop, install per local instructions, restart a fresh empty document and mcpstart, then acknowledge this request hash. Never replace a loaded assembly.",
    }
    ticket_path = request_path.with_name(request_path.stem + "-lifecycle.json")
    ack_path = request_path.with_name(request_path.stem + "-ack.json")
    persist(ticket_path, ticket)
    print(f"Lifecycle handoff: {ticket_path}", flush=True)
    deadline = time.monotonic() + 900
    while not ack_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("Desktop lifecycle handoff was not completed")
        time.sleep(0.5)
    if read(ack_path) != {"request_sha256": ticket["request_sha256"]}:
        raise ValueError("Lifecycle acknowledgement does not match the pending request")
    after = claim_empty(directory)
    if after["pid"] == before["pid"]:
        raise RuntimeError("Lifecycle did not restart the dedicated Rhino process")
    if probe(directory) != request["expected_identity"]:
        raise RuntimeError("Restart loaded the wrong binary")
    return {"restarted": True, "pid": after["pid"]}


def build(request):
    directory = Path(request["trial"])
    workspace = directory / "build-workspace"
    shutil.copytree(request["source"], workspace)
    commands = [
        ["dotnet", "build", "plugin/rhinomcp.sln", "--configuration", "Release"],
        [
            sys.executable,
            "-m",
            "pytest",
            "server/tests",
            "contracts/test_schemas.py",
            "-q",
        ],
        [sys.executable, "-m", "ruff", "check", "server/src/rhinomcp"],
    ]
    for command in commands:
        subprocess.run(
            command,
            cwd=workspace,
            check=True,
            timeout=180,
            env={**os.environ, "PYTHONPATH": str(workspace / "server/src")},
        )
    if read(Path(request["suite"])).get("sweep_cap_probe") is True:
        from experiments.validate_sweep_source import validate

        save(directory / "sweep-source-validation.json", validate(workspace))
    binary = workspace / "plugin/bin/Release/net8.0/rhinomcp.rhp"
    shutil.copy2(binary, request["candidate_binary"])
    helper_output = directory / "metadata-reader"
    subprocess.run(
        [
            "dotnet",
            "build",
            str(ROOT / "experiments/assembly_identity/assembly_identity.csproj"),
            "-o",
            str(helper_output),
            "--nologo",
        ],
        check=True,
        timeout=120,
    )
    return json.loads(
        subprocess.check_output(
            [
                "dotnet",
                str(helper_output / "assembly_identity.dll"),
                request["candidate_binary"],
            ],
            text=True,
        )
    )


def fixture_verdicts(kind, reports):
    valid = {
        "box": {"correct"},
        "prism": {"correct", "split_face"},
        "hole": {"correct_extrusion", "correct_brep", "correct_oversized_cutter"},
    }[kind]
    return {
        f"geometry/{kind}/{name}": report["status"]
        == ("pass" if name in valid else "fail")
        and report["repeat_identical"] is True
        for name, report in reports.items()
    }


def test_suite(request):
    directory = Path(request["trial"])
    observed = probe(directory)
    if observed != request["expected_identity"]:
        raise ValueError("Wrong runtime before testing")
    state = runtime()
    if state["object_count"] or state["path"]:
        raise RuntimeError("Live suite requires the empty dedicated document")
    report_dir = directory / ("live-" + uuid.uuid4().hex[:8])
    report_dir.mkdir()
    cases, evidence = {}, {}
    for kind, validator in [
        ("box", validate_box),
        ("prism", validate_prism),
        ("hole", validate_hole),
    ]:
        result_dir = validator()
        report_path = result_dir / "validation.json"
        cases.update(fixture_verdicts(kind, read(report_path)))
        evidence[kind] = {"path": str(report_path), "sha256": sha256(report_path)}
    # The fixed prism fixture is independently generated, not a modeler output.
    prism_path = Path(evidence["prism"]["path"]).parent / "correct.3dm"
    before_captures = set((ROOT / "experiments/runs").glob("capture-validation-*"))
    capture_validate(prism_path)
    new_captures = (
        set((ROOT / "experiments/runs").glob("capture-validation-*")) - before_captures
    )
    if len(new_captures) != 1:
        raise RuntimeError("Ambiguous capture evidence directory")
    capture_dir = new_captures.pop()
    captures = read(capture_dir / "validation.json")
    cases.update(
        {"capture/" + name: case["passed"] for name, case in captures["cases"].items()}
    )
    evidence["capture"] = {
        "path": str(capture_dir / "validation.json"),
        "sha256": sha256(capture_dir / "validation.json"),
    }
    clear_owned(directory, capture_dir.name)
    task_root = ROOT / "experiments/tasks"
    tasks = [
        (name, task_root / (name + ".json"))
        for name in ["box", "posed_prism", "through_hole", "reference_box"]
    ]
    swapped = load_task(task_root / "reference_box.json")
    swapped["id"] = "reference-box-swapped-v1"
    swapped["dimensions"] = [40, 70, 30]
    swapped_path = report_dir / "reference-swapped.json"
    save(swapped_path, swapped)
    tasks.append(("reference_box_swapped", swapped_path))
    for name, task in tasks:
        print("Modeling " + name, flush=True)
        run_dir, summary = run_locked(task, 180, ROOT / "experiments/runs")
        cases["model/" + name] = summary["evaluation"] == "pass"
        evidence[name] = {
            "path": str(run_dir / "summary.json"),
            "sha256": sha256(run_dir / "summary.json"),
        }
        if name == "reference_box_swapped":
            wrong = evaluate(
                load_task(task_root / "reference_box.json"),
                measure(run_dir / "candidate.3dm"),
            )
            save(report_dir / "negative-control.json", wrong)
            cases["control/reference_equal_volume_wrong_dimensions"] = (
                wrong["status"] == "fail"
                and wrong["checks"]["volume"]
                and not wrong["checks"]["dimensions"]
            )
        clear_owned(directory, run_dir.name)
        save(report_dir / "progress.json", {"cases": cases, "evidence": evidence})
    contract = read(Path(request["suite"]))
    if contract.get("sweep_cap_probe") is True:
        from experiments.sweep_cap_probe import run_checks

        cases.update(run_checks(report_dir / "sweep-cap", runtime()))
        evidence["sweep_cap"] = {
            "path": str(report_dir / "sweep-cap/result.json"),
            "sha256": sha256(report_dir / "sweep-cap/result.json"),
        }
    if set(cases) != set(contract["cases"]):
        raise ValueError("Live suite case names do not match the frozen contract")
    if probe(directory) != observed:
        raise RuntimeError("Runtime changed during the live suite")
    result = {"identity": observed, "cases": cases}
    save(report_dir / "result.json", {**result, "evidence": evidence})
    print(f"Live report: {report_dir}", flush=True)
    return result


def main_locked():
    request_path, response_path = map(Path, sys.argv[1:])
    request = read(request_path)
    directory = Path(request["trial"])
    action = request["action"]
    if action == "probe":
        result = probe(directory)
    elif action == "build":
        result = build(request)
    elif action == "test":
        result = test_suite(request)
    elif action in ("install", "restore"):
        result = lifecycle(request, request_path)
    else:
        raise ValueError("Unknown live action")
    persist(response_path, result)


def main():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        main_locked()


if __name__ == "__main__":
    main()
