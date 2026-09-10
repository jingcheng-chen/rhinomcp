# Workflow family allocation

Declared 2026-09-09 before any M2 agent discovery run.

Discovery: editing an existing solid, a named/layered small assembly, inspection
of a prepared document without mutation, and recovery from a wrong intermediate.
The assembly overlaps historical layer-organization evidence and is not claimed
unseen. Existing primitive, pose, boolean, patch and panel families remain spent.

Reserved for later validation, not opened or run in M2:

- planar curve editing through offset and fillet operations;
- section extraction from existing solids and organization of the resulting curves.

No reserved parameterizations are disclosed to M2 modelers. These families are
reserved relative to this agent-discovery bank, not claims that the underlying
production tools were never unit-tested. Record use before spending a family and
replace it after validation. The allocation log below records subsequent use.

## M3-1 allocation — 2026-09-10, before validation

Planar curve editing is allocated to cycle 1 validation using a prepared closed
outline and an outward offset. This case exercises offset editing; filleting is
not claimed covered. Parameters are fixed in `tasks/offset_outline.json` by the
supervisor after planner proposal, and are not supplied to the bounded builder.
It becomes spent when the first comparison modeler starts. Section extraction
remains reserved for cycle 2. Replacement bank: curve-network joining and
instance/block reuse (no parameters opened or runs yet). Lofted shells were dropped before use because they overlap prior surface discovery.

M3-1 suite frozen for its first modeler dispatch on 2026-09-10. The planar
curve-editing family is now spent for subsequent discovery/tuning; all AB/BA
attempts in this one frozen validation remain part of its declared use.

## M3-2 allocation — 2026-09-10, before validation

Section extraction is allocated to cycle 2. After the fresh planner proposal, the
supervisor fixes a prepared solid and two section heights in
`tasks/extract_sections.json`. The bounded builder receives no task parameters.
Eight saved controls calibrate the shared evaluator before comparison. This
family becomes spent at the first dispatch of the frozen cycle 2 comparison;
curve-network joining and instance/block reuse remain unopened replacements.

The frozen M3-2 comparison dispatched its first modeler on 2026-09-10. Section
extraction is now spent for later tuning; all twelve runs belong to this allocation.

## M4 sealed bank — 2026-09-10

Source of truth: [held-out-bank.json](held-out-bank.json), managed by
`held_out.py`. The M3 entries are explicitly imported historical spends, backed by
unchanged task/result hashes; this does not retroactively claim a cryptographic
reservation before M3. Both have a sealed replacement and are closed as kept.

| Family | State | Fixed cases | Replaces |
| --- | --- | --- | --- |
| Planar curve editing | Spent in M3-1 | Historical offset task | — |
| Section extraction | Spent in M3-2 | Historical section task | — |
| Curve-network joining | Sealed, available | 2 | M3-1 |
| Instance/block reuse | Sealed, available | 2 | M3-2 |

Private bundles are in ignored `experiments/held_out_private/`, with owner-only
permissions. Do not open them for discovery, send them to a planner/builder, place
them in public task directories, or infer new variants after seeing outcomes.
Public metadata records the novelty review, case count and payload hash. Sealing
here means supervisor custody and an immutable commitment, not encryption or an
adversarial filesystem boundary. Fresh bounded roles cannot request these paths
through their tools. A supervisor with filesystem access can read them; M5 remains
necessary for hard isolation. Keep a private backup when moving workspaces. A
fresh clone without the bundles reports `unavailable`, never validation-ready.

### Allocate one family to one frozen validation

1. Inspect metadata with `server/.venv/bin/python -m experiments.workflow.held_out status`.
   Check the public exclusion list and semantic novelty review, not just the name.
   Renaming a family or choosing new dimensions does not make it held out again.
2. Complete the fresh planner/builder boundaries and write the validation review
   before opening a bundle. It must declare the two discovery families, selected
   held-out family, agent/budgets, calibration plan, fixed comparison design and
   keep rule. Do not give the builder the private parameters.
3. Run the following with a new validation ID and a new output path:

   ```sh
   server/.venv/bin/python -m experiments.workflow.held_out spend ENTRY_ID --validation VALIDATION_ID --review-file REVIEW.md --output SUPERVISOR_BUNDLE.json
   ```

   The ledger marks the **entire family spent before export**, conservatively
   earlier than first modeler dispatch. All cases may be used in that one frozen
   validation, but no tuning or extra repetitions after seeing results. Commit the
   ledger and preserve its hash with the comparison review before modeling.
4. Independently turn the committed specification into the shared task/evaluator
   route and calibrate saved positive/negative controls. These sealed specifications
   are not yet runnable task schemas or calibrated geometry evaluators. Do not
   loosen the fixed acceptance requirements to pass a run. If preparation exposes
   an invalid case, retain it as abandoned and replace the family. Freeze runnable
   task/evaluator/catalog/source pins before modeler dispatch through the existing
   comparison controller; this bank never launches agents or changes Rhino.
5. Preserve every outcome, including timeout, failure and abandonment. Seal a new,
   semantically unused family with `seal PRIVATE_SPEC.json --replaces ENTRY_ID`,
   then `close ENTRY_ID --outcome OUTCOME --report REPORT` (outcome: kept, rejected,
   incomplete or abandoned).
   Those subcommands use the same module invocation as above. Closing requires a
   still-available sealed replacement; no command restores a spent family.

An export failure still spends the family. `export ENTRY_ID --validation SAME_ID
--output NEW_PATH` can recover the identical bundle for the same open validation;
it never grants a new attempt. A leaked, missing or damaged bundle is retired with
`retire ENTRY_ID --validation INCIDENT_ID --review-file INCIDENT.md`, without
reading/exporting its contents. Replace it and close it as abandoned. Public
ledger edits or payload mismatches are not repaired by regenerating parameters.

The CLI enforces allocation state and byte identity. It does not prove semantic
novelty, calibrate geometry, prevent a supervisor from bypassing it, or replace the
comparison controller's immutable schedule. See [M4 validation](M4.md).

## M3b-1 allocation — 2026-09-10

`curve-network-joining-v1` was spent through the ledger after the fresh planner,
bounded builder and independent description-only source review. Both cases are
fixed in the shared scene schema; 27 saved controls match their expected verdicts,
including reversed-order equivalents and connectivity/reference failures. The
predeclared review is `M3B_CYCLE1_REVIEW.md`; source/catalog checks are in
`m3b-cycle1-source-validation.json`, calibration in `m3b-curve-calibration.json`.
The family is spent for this validation only; no replacement or closure yet.

M3b-1 validation is closed as rejected against the immutable
`m3b-cycle1-results.json` hash. All 16 Codex saved outputs pass, but the efficiency
and failed-call rule fails; the four scheduled Claude attempts are recorded too.
`directional-curve-projection-v1` supplies two sealed replacement cases and remains
available. Instance/block reuse is still unopened.

## M3b-2 allocation — 2026-09-10

After fresh planner/builder and independent description-only review,
`directional-curve-projection-v1` was spent for M3b-2. Both specifications have
faithful shared-scene task adapters. Thirty-two saved controls match expected
verdicts, including reversed equivalents and direction, height, source/target,
edge and layer failures. See `M3B_CYCLE2_REVIEW.md` and
`m3b-projection-calibration.json`. No comparison modeler has run at allocation.

## M3b closure, 2026-09-10

Both joining and directional projection are spent and closed as rejected. Their
immutable outcome reports are `m3b-cycle1-results.json` and
`m3b-cycle2-results.json`. Projection replaced joining, and mesh connectivity
repair replaced projection before closure. Instance/block reuse and mesh repair
remain unopened and require future shared-adapter calibration. M5 is deferred.
