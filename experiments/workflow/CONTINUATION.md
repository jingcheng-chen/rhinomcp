# Verified comparison continuation

The binary comparator records an immutable modeling checkpoint after each fully
accounted session. A checkpoint contains completed rows, resource totals, environment
settings and hashes of modeling inputs, files, screenshots and logs. State records
the checkpoint hash. `run --max-sessions N` pauses at a completed boundary and restores
the baseline; `resume` continues the remaining frozen schedule in a new controller.

Continuation checks the complete prefix, unchanged source/catalog/contract pins,
artifacts and resource ledger before touching Rhino. It restores/verifies the trusted
baseline before continuing. It never repeats a modeling call or a completed session.
An active or unaccounted session, uncheckpointed output directory, altered receipt,
changed environment, exhausted allowance or partially started evaluation blocks it.
There is no automatic retry of a failed session and no continuation of a provider
conversation. Restore and inspect ambiguous work separately. Judging interruption
recovery is deliberately not inferred from a partly written verdict.

## Live validation

`runs/workflow-binary-20260908-220720-3c737caa` paused after one fresh box session.
A separate controller resumed exactly the remaining three sessions. The first
checkpoint hash is unchanged. Four distinct modeling sessions pass, with 13 total
attempts and 71.94 modeling seconds. Two supervised process/binary transitions pass;
the selected planar-region baseline is restored before every saved-file judgment.
All models, screenshots, resources and evidence hashes are retained. Source inputs
were archived before later development. See `checkpoint-results.json` and the
four actual images on the roadmap.

This is controller validation with a fixed simple task, not evidence to select the
older binary or infer capability benefit from its small call-count fluctuation.
Eleven fault/integration tests cover pauses, process loss after a durable checkpoint,
uncertain dispatch, changed evidence, ledger drift and attempted completed-run replay.
