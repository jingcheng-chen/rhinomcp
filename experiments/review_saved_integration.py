"""Supervised recovery after the observed File3dm LINQ audit failure; no remodeling."""

import json
import shutil
from experiments.bridge import script, assert_document
from experiments.integration_audit import review_evidence, audit
from experiments.integration_runner import (
    pinned_inputs,
    configuration,
    structural_report,
)
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256, run_session, PLANNER_SCHEMA
from experiments.model_screenshots import capture_shaded
from experiments.trial import locked


def run(directory):
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = json.loads((directory / "environment.json").read_text())["rhino"]
        require_owned(runtime(), owner)
        assert_document(owner["document"], directory.name)
        if (directory / "summary.json").exists():
            raise RuntimeError("Review already completed")
        if (
            json.loads((directory / "modeler/status.json").read_text())["status"]
            != "completed"
        ):
            raise RuntimeError("Modeler must have finished")
        old = json.loads((directory / "inputs.json").read_text())
        pins = pinned_inputs()
        changed = {n for n in old.keys() | pins.keys() if old.get(n) != pins.get(n)}
        if changed != {"experiments/integration_audit.cs"}:
            raise RuntimeError("Unexpected implementation changes")
        for name in pins:
            dst = directory / "recovery-source" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dst)
        save(directory / "recovery-inputs.json", pins)
        (directory / "recovery-source/review_saved_integration.py").write_bytes(
            (ROOT / "experiments/review_saved_integration.py").read_bytes()
        )
        task = json.loads((directory / "task.json").read_text())
        claim = json.loads((directory / "modeler/result.json").read_text())
        refs = json.loads((directory / "references/public.json").read_text())
        for meta in refs["views"].values():
            if sha256(directory / "references" / meta["file"]) != meta["sha256"]:
                raise RuntimeError("Reference changed")
        artifact = directory / "candidate.3dm"
        digest = sha256(artifact)
        measured = json.loads(
            script(
                (ROOT / "experiments/visual_audit.cs")
                .read_text()
                .replace("ARTIFACT_PATH", json.dumps(str(artifact)))
            )
        )
        report = structural_report(task, measured)
        report["integration"] = audit(artifact)
        report["artifact_sha256"] = digest
        save(directory / "evaluation.json", report)
        save(
            directory / "recovery.json",
            {
                "reason": "File3dm object LINQ projection raised NullReferenceException. Equivalent explicit iteration completed repeated reads; no acceptance predicate changed. Underlying API cause not established.",
                "changed": sorted(changed),
                "artifact_sha256": digest,
                "remodeled": False,
            },
        )
        script(
            "foreach(var view in doc.Views) view.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(Rhino.Display.DisplayModeDescription.ShadedId);doc.Views.Redraw();"
        )
        capture_shaded(directory, owner["document"], directory.name)
        save(
            directory / "checkpoint.json",
            {"stage": "reviewing", "owner": owner, "marker": directory.name},
        )
        review = run_session(
            directory / "planner",
            "You are the independent diagnostic planner. Inspect all four public reference images and the candidate in perspective, right and back views using get_reference_image(view) and inspect_view(view) on rhino_experiment. Do not guess local image paths. If these tools are unavailable, explicitly report that image review could not be completed. Compare visible shape and classify modeling choices, reproducible tool defects and evaluator limits. Visual acceptance remains unscored. Recommend one small transferable next experiment; preserve the 61-case production repair suite. Do not claim a plugin defect from a geometric mismatch alone. The first audit hit an iteration error, corrected by the supervisor without changing predicates or the saved model.\n"
            + json.dumps({"task": task, "claim": claim, "audit": report}),
            PLANNER_SCHEMA,
            300,
            configuration(directory, owner, directory / "references", 30, True),
        )
        require_owned(runtime(), owner)
        assert_document(owner["document"], directory.name)
        if sha256(artifact) != digest or pins != pinned_inputs():
            raise RuntimeError("Review input changed")
        save(
            directory / "summary.json",
            {
                "task": task["id"],
                "evaluation": "unscored",
                "modeler_claim": claim,
                "modeler_error": None,
                "planner": review,
                "review_evidence": review_evidence(directory),
                "artifact_sha256": digest,
                "plugin_changed": False,
                "promoted": False,
                "structural_checks": report["structural_checks"],
                "integration": report["integration"],
                "audit_recovery": "recovery.json",
            },
        )
        save(
            directory / "checkpoint.json",
            {"stage": "completed_diagnostic", "owner": owner, "marker": directory.name},
        )
        return directory
