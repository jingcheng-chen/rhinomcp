# Guarded experimental selection and rollback

`experiments/selection.py` connects an accepted declared-capability trial to a
completed trusted-baseline workflow comparison. It requires all candidate repeats
to pass, no task correctness regression, observed workflow benefit, a reserved case
outside the declared discovery tasks, and preservation in another task family.
The claim is scoped benefit, not broad unseen-family generalization.

Preparation verifies the original trial inputs from archived copies, the unchanged
candidate source and patch, comparison pins, binary identities, saved artifact hashes
and evaluation consistency. A nonempty supervisor review records the intended scope.
The production checkout must match the reviewed baseline; unrelated production edits
or undeclared source additions block preparation. No production file is changed by
preparation.

The journal preserves exact before/after bytes and modes for the declared files.
Application writes durable intent before changing sources and uses atomic replacement.
Rollback accepts only known before/after states, including interrupted partial writes;
it refuses to overwrite later user edits. Source writes take the shared Rhino lock,
so they cannot invalidate an active modeling experiment. Reapplying after an explicit
rollback is allowed; it does not replay modeling sessions or alter original evidence.

Runtime activation uses a separate lifecycle record inside the selection journal.
After source application, `switch-runtime` issues the existing hash-bound supervised
quit/copy/restart ticket. The first switch requires a fresh empty dedicated document.
Only matching loaded MVID, installed binary hash, empty document and selected source
hashes allow runtime confirmation. Roll back sources, then call `switch-runtime`
again to restore the previous binary. Completed comparison records are never reused
as mutable installation records.

Nineteen focused tests cover source round trips, interrupted writes, later user edits,
path/snapshot drift and incomplete, regressed or inconsistent validation evidence.
The planar-region selection exercised production source and runtime activation,
rollback to the exact original catalog/binary, and reactivation. Receipts are in
`runs/selection-20260908-214357-b9bfc9f6`; see `planar-region-selection.json`.
This is a local integrity mechanism for reviewed candidates, not an adversarial OS
sandbox or unattended promotion system. A bounded reviewed comparison queue is implemented separately in `CAMPAIGN.md`.
Hard isolation and unattended promotion remain separate work.
