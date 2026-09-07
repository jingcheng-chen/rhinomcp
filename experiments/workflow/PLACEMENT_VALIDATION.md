# Reserved placement validation — prepared 2026-09-07

Two new cases are frozen before agent execution:

| Family | New input |
| --- | --- |
| Primitives | 64 × 36 × 22 mm box; minimum (−110,45,−28) mm |
| Subtractive solids | 72 × 44 × 18 mm block; minimum (140,−80,35) mm; radius-4.5 through-hole at XY (161,−63) |

These are new cases within the same two families, not a new unseen family. The
candidate text is byte-identical to the discovery trial. Model alias, reasoning,
budget, two counterbalanced pairs, evaluator tolerances and acceptance criterion
are unchanged. The planned eight agent runs have **not run**.

Independent in-memory fixtures calibrate the unchanged evaluator at these offsets.
For each task, the correct fixture passes and a deliberately misplaced fixture
fails. Each verdict repeats identically. The wrong hole retains the correct radius
and volume but shifts its axis by 1 mm, verifying position-sensitive rejection.
The active Rhino document fingerprint is unchanged by calibration.

A first calibration preflight stopped because the active document was no longer
the experiment document. Read-only fixture construction can safely run in memory;
it does not require replacing the active document. An initial hole fixture generator
then failed when adding an inner profile at the elevated plane. The corrected generator
constructs the profile locally and translates the completed solid. No evaluator,
production behavior or acceptance criterion changed. Failed attempts remain local.

Final calibration: `experiments/runs/placement-validation-controls-20260907-160041/`.
It retains the generator, synthetic files, repeated reports and preservation evidence.
The [tracked calibration summary](placement-validation-controls.json) retains verdicts
and the generator hash without including the user's model contents.

## Live execution boundary

Rhino currently has a saved packaging document open alongside the empty experiment
document. The existing shared harness requires one dedicated unsaved document and
rejects this state. No user document was closed, cleared or changed. The agent trial
is pending availability of Rhino for exclusive testing; do not weaken the ownership
checks or silently switch documents.

Once the user makes Rhino available, recheck process/document state and run:

```sh
PYTHONPATH=/absolute/path/to/rhinomcp server/.venv/bin/python -m experiments.workflow.compare experiments/workflow/placement-validation-trial.json
```

Keep the prior positive discovery result separate. Do not adopt the description into
production until this validation is completed and reviewed. Record every outcome,
including failures or ties. No new model screenshots exist in this preparation phase;
the roadmap retains the previous eight agent outputs.

Verification: **489 tests pass**, with 12 existing warnings. New checks ensure that
reserved cases change dimensions/positions while retaining evaluator types/tolerances,
and that the candidate hash and agent settings match discovery. No build or installation
was performed. Production code and the tested candidate remain unchanged.
