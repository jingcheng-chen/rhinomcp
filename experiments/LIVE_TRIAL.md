# Live Rhino trial adapter

The adapter is `rhino_trial.py`. It builds candidates, reads assembly metadata
without executing the binary, checks the loaded Rhino assembly, and runs the
fixed 43-case suite. The supervising desktop agent performs the actual application
quit/install/restart steps in response to a recorded lifecycle ticket. This is
controller-orchestrated **supervised lifecycle**, not unattended installation.

## Ownership and lifecycle

Start with exactly one empty, unmodified, unsaved Rhino document. After preparing
a trial, call `rhino_trial.claim_empty(trial_directory)` to record its process ID
and document serial. The adapter refuses a different process/document, a saved
document, or additional open documents. The existing modeling lock spans each
adapter invocation; fresh modeler sessions run inside the suite's ownership scope.
Only the marked dedicated task document is cleared between tasks.

An install or restore invocation creates `<request-stem>-lifecycle.json` alongside
the request. It identifies the target binary, expected SHA-256/MVID, previous
runtime, and request hash. The supervisor must:

1. Verify the current dedicated process/document against the ticket. Do not quit
   an unrelated document or replace an assembly still loaded in Rhino.
2. Quit through the desktop, follow the machine-local plugin installation rule,
   launch Rhino, create a fresh empty document, and start `mcpstart`.
3. Write `<request-stem>-ack.json` containing exactly
   `{"request_sha256": "the pending request hash"}`.

The adapter then requires a different process ID, exactly one fresh empty document,
and a matching loaded MVID and installed-file hash. Merely writing an acknowledgement
does not pass those checks. Ticket waiting is bounded; a stopped Rhino can still produce a supervised restore ticket using the recorded
owner. A reachable foreign process or a nonempty document remains a hard stop.

The local wrapper sets the repository import path and calls the tracked adapter:

```python
import sys
sys.path.insert(0, "/absolute/path/to/rhinomcp")
from experiments.rhino_trial import main
main()
```

The wrapper path is passed to `trial.py prepare --adapter`. The tracked module,
metadata-reader source and project are declared suite inputs and pinned. The
installation destination remains solely in local instructions, not this adapter.

## Fixed suite and build

The adapter runs all 26 fixture verdicts (each measured twice), all 11 captures,
and five fresh modeler/planner loops: box, posed prism, through-hole, reference box
and swapped reference box. The swapped model is also checked against the original
reference task: equal volume must pass while dimensions fail. This yields 43
mandatory verdicts, each backed by saved local evidence.

Candidate builds run in a separate copy of the reviewed source. Python developer
checks import the candidate's server code. `assembly_identity` reads PE metadata
and SHA-256 without loading candidate code; only the reviewed local installation
step loads the candidate into Rhino. The full suite runs before installation,
after installation, and after restoration.

## Launch correction found during integration

The first live attempt failed before installation because the trial controller
resolved the virtual environment's Python symlink and invoked the underlying
interpreter directly. That bypassed the environment's RhinoMCP dependencies.
The controller now invokes the original virtual-environment path while separately
pinning its resolved binary. A regression test executes an adapter importing the
project package. The failed attempt is retained, rather than rewriting its record.

## Reusing an empty document after deletion

The second integration attempt passed 26 fixtures and 11 captures, then stopped
before installation: `RhinoObjectTable.Count` included an undoable-deleted object.
Direct inspection showed one table slot but zero active objects. Some LINQ array
operations also exposed a null deleted slot. Harness identity, capture-state and
cleanup queries now explicitly exclude null/deleted objects. Saved-model geometry
predicates are unchanged. Fresh acceptance runs retain the new evaluator-source
hashes; the failed historical trial is not rewritten.

The dedicated document may remain marked modified because its undo transaction
records the test's cleanup. Lifecycle requests require owned identity, no active
objects, and no remaining task marker; the supervisor discards only this known
trial document. Initial/restarted ownership still requires a fresh empty document.

## Controller-side capture measurements

A subsequent baseline attempt timed out in Rhino's per-pixel `Bitmap.GetPixel`
scan. `validate_capture.pixel_bounds` now uses Pillow in the controller. The rule
is identical (all RGB channels strictly below 80); bounds and count match all ten
PNG measurements in `capture-validation-20260905-221007/validation.json` exactly.
The independent scan took about 0.25 seconds for that set. Evidence is retained in
`runs/pixel-equivalence.json`. Pillow is a declared development dependency.

## Restart connection correction and build gates

The first actual candidate restart loaded the expected binary, but the waiting
adapter still held its connection to the exited Rhino process. Its identity call
failed before ownership could move to the new process. The supervisor restored
and verified the baseline, recording `operator-restoration.json` in that trial.
The adapter now disconnects before issuing the lifecycle ticket. Tests require
that disconnection precede claiming the restarted process. The failed trial's
checkpoint remains intact; it is not counted as a completed controller rollback.

The build gate also exposed 18 pre-existing E701 formatting issues in four Python
tool files. Formatting-only commit `e41c257` corrected them; all 223 server tests
passed and the full server lint check passes. The repository-wide format check
still reports 17 other pre-existing files; these were not reformatted as part of
the live adapter work. Candidate build checks are compilation, 235 Python/contract
tests and lint, not a claim that all repository formatting checks pass.

## Test process coordination

Run repository tests and candidate developer tests sequentially. The existing
integration-test mock server uses a fixed local port. One integration attempt
collided with a concurrent repository test run and was rejected before installation
(178 passed, 57 fixture errors). No acceptance rule was changed; the subsequent
attempt runs without the competing test process.

## Verification record

The deliberately failing candidate is a fresh supervisor-authored fault injection:
replace the `zoomToFit` parameter assignment in the isolated candidate's
`CaptureViewport.cs` with `bool zoomToFit = false;`. The bounded candidate passes
source review, compilation (zero warnings/errors), 235 candidate Python/contract
tests and lint. This is recovery validation, not an agent-generated improvement or
a reopened historical builder trial. Production C# plugin source is unchanged.

Local trial: `runs/live-recovery-20260905-224344/trial-dc347a7d/`.
The baseline passes 43/43. The candidate passes 34/43: all nine fitted capture
cases fail, while 26 fixture verdicts, two remaining capture checks, five fresh
modeling runs and the equal-volume negative control pass. `comparison.json`
records the exact regressions. No rule or pinned source changes during this trial.

| Runtime | Loaded MVID | Binary SHA-256 |
| --- | --- | --- |
| Baseline | `90d87782-2887-435e-a8b2-02467f0c5094` | `ac4699e049474f41adcae08a6b8226eb84a65de573e1de82bf238ebeb8491a35` |
| Deliberate regression | `e6a04287-d1e6-40f7-976f-8974f6b17f3b` | `9844a40da11a16ba6fe8605c8c81a9a3d72c1e2a1196ed5b1696389a8f280e2b` |

After comparison, the supervisor deliberately terminates the controller and its
idle adapter at restore ticket `020-restore-dfac7a`, before any physical restoration.
Their exact commands/PIDs and stopped state are checked and recorded in
`operator-interruption.json`; `interruption-before.json` preserves the regression
checkpoint. A run without acknowledgement returns `operator_required` and retains
the pending request (`interruption-blocked.json`). Only after verifying both
processes stopped does the supervisor resume with:

```sh
server/.venv/bin/python -m experiments.trial run /absolute/path/to/trial-ID \
  --timeout 1800 --ack-child-stopped
```

The controller creates a new restore request (`025-restore-429aa4`), with no replay
of candidate installation. The supervisor services that ticket and verifies the
baseline loaded in a new Rhino process. This exercises interruption at the recovery
handoff, not a crash midway through copying a plugin file. The initial candidate
rejection remains in `comparison.json`, even though resumed state records the
interruption as its final error reason.

The restored baseline passes **43/43**. Final controller stage is `rejected`,
`runtime_dirty=false`, `promoted=false`; all `restored_cases` are true. There is
one candidate install and one completed restoration. The interrupted restore
request has no acknowledgement/response and is never replayed. Final loaded
identity and empty owned document are recorded in `final-runtime.json`.

| Fixed checks | Baseline | Faulty candidate | Restored baseline |
| --- | ---: | ---: | ---: |
| Geometry fixture verdicts, each repeated | 26/26 | 26/26 | 26/26 |
| Capture framing and preservation | 11/11 | 2/11 | 11/11 |
| Fresh modeling runs | 5/5 | 5/5 | 5/5 |
| Equal-volume wrong-dimensions control | 1/1 | 1/1 | 1/1 |
| Total | **43/43** | **34/43** | **43/43** |

Suite evidence folders in the trial are `live-c68a6d8e` (baseline),
`live-e4ddffc8` (candidate) and `live-0f84328c` (restored baseline). Each retains
`result.json` with hashes/paths to underlying measurements and agent runs.
Rhino is left running the original working plugin with an empty owned unsaved
document; verify identity and contents again before reuse.

Developer verification: **338 passed** (115 experiment, 223 server), including
lifecycle ownership/acknowledgement/restart checks, stopped-runtime recovery ticket,
virtual-environment execution and strict pixel threshold tests. Experiment lint and
format checks, full server lint and schema validation pass. The full server format
check has the pre-existing limitation described above. Full local evidence remains
ignored; these results are historical verification, not a substitute for rerunning
on another machine.
