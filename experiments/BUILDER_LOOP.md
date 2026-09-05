# Isolated builder pilot

Completed live on 2026-09-05 on the `harness` branch.

## Implemented workflow

`repair.py` replays the recorded capture defect from pinned source revision
`a7bd5d1`. It exports only `plugin/`, `server/` and `contracts/` into an independent
checkout with its own Git metadata. The checkout contains no harness evaluators,
reference answers or connection back to the working repository's Git metadata.

A fresh planner diagnoses the development evidence. Only `plugin_issue` permits
builder dispatch. The new `evaluator_issue` action is schema-valid and routes to
supervision instead. A separate live planner session correctly diagnosed the old
trimmed-face measurement defect as `evaluator_issue`; dispatch was refused.

The builder is a fresh Codex CLI session with shell and unrelated tools disabled.
Its MCP gateway exposes only exact-path source reads and compare-before-write
replacements. It can read four specified source files and edit three:

- `plugin/Functions/CaptureViewport.cs`
- `server/src/rhinomcp/tools/capture_viewport.py`
- `contracts/commands/capture_viewport.json`

`plugin/Functions/_utils.cs` is readable only. There are no build, Rhino, install,
file-creation or evaluator tools. Writes have size limits, reject symlinks and
require the last-read hash. A controller inventory covers the entire checkout,
including Git metadata: additions, deletions, mode changes and edits outside the
allowlist fail before candidate code can be executed. Concurrent tool writes are
serialized; review invocations use an exclusive writer lock.

The adapter stops at `candidate_ready_for_review`. A reusable `--revise` path
starts another fresh builder session with controller feedback, preserves the
input patch and feedback, checks the prior patch identity, and reapplies the
whole-checkout integrity gate. It refuses active or already-executed candidates.
A completion claim is not an acceptance verdict.

## Live repair and validation

Pilot directory: `runs/repair-20260905-211537-bc56415e/` (local, ignored by Git).
The baseline evidence was retained from `capture-validation-20260905-202746`:
four of nine fitted images clipped, and all ten successful captures changed
camera state. This is a replay of a known defect with supervisor-supplied Rhino
API clues, not a claim of novel bug discovery or model training.

The first builder patch changed only C#. Supervisor review requested explicit
handling of fitting API failures and corrected Python/schema descriptions. A
second fresh builder session made those changes. The final patch touched exactly
the three allowed files. The supervisor inspected it before execution.

The supervisor then performed the following validation outside the builder:

- Candidate Release build: zero warnings/errors.
- Candidate server tests: 223 passed; schema synchronization and relevant lint passed.
- Installation with Rhino closed, followed by restart and loaded binary identity check.
- All 11 fixed capture checks passed (`capture-validation-20260905-212313`).
- All 26 geometry fixtures returned expected verdicts twice (`evaluator-box-20260905-212424`,
  `evaluator-prism-20260905-212430`, `evaluator-hole-20260905-212433`).
- Fresh modeler/evaluator/planner prism loop passed (`20260905-212501-e2ef7a97`).
  Its saved PNG has 11,807 dark geometry pixels, bounded by X=45..954 and Y=185..592.

| Assembly | Loaded MVID |
| --- | --- |
| Archived failing baseline | `243974ba-3378-4df8-88b6-fd4dba066ebc` |
| Builder candidate | `e7e17267-3a6a-45e4-b37f-869810ee216d` |
| Working baseline restored after trial | `90d87782-2887-435e-a8b2-02467f0c5094` |

The previous working binary was backed up before trial, then restored with Rhino
closed and verified after another restart by both MVID and file hash. The working
repository's production source was not replaced. No candidate was promoted.
The pilot checkpoint records `completed`, trial pass, baseline restored and no promotion.

Records include the plan, both builder sessions, correction feedback, final patch,
source inventory, developer-check logs, supervisor review, loaded identities,
validation report and verified restoration. The archived baseline was not rebuilt
again during this pilot; comparison uses its previously recorded live evidence.

## Verification and remaining limits

The root suite passes 304 tests (81 experiment and 223 server tests). Boundary tests
cover evaluator-route refusal, arbitrary paths, stale writes, symlinks, protected
files, additions/deletions/modes, review lifecycle, independent fresh review sessions,
and exclusive review writers. Experiment lint and formatting checks pass.

Source editing and the review handoff are automated. Code review, build, installation,
live validation and restoration were performed by the supervising development session.
This is not an unattended repair/deploy/rollback controller. The candidate was tested
on development fixtures, not a held-out generalization suite.

The tool boundary restricts the agent's editing capabilities; it is not a new OS
security boundary. After review, candidate code runs inside Rhino with normal plugin
privileges. Trusted measurement still uses the same process, so a malicious plugin
could interfere with it. Stronger evaluator isolation and controller-owned validation
are required before accepting unreviewed candidate execution or automatic promotion.
