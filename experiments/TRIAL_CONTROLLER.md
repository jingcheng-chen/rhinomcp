# Candidate validation and recovery controller

Implemented on 2026-09-05. This milestone verifies orchestration with real adapter
subprocesses and a disposable **file-based runtime**, not a live Rhino installation.
The previous live builder pilot remains documented in `BUILDER_LOOP.md`.

## What is implemented

`trial.py prepare` consumes an unexecuted builder candidate ready for review. It
checks the whole checkout and exact patch against the builder checkpoint, saves a
separate source snapshot, baseline binary and review record, and registers the
trial so `repair.py --revise` cannot modify it. A reviewed candidate must not be
prepared while a builder is still active.

The manifest pins the patch, source inventory, baseline bytes/MVID, adapter script,
Python executable, suite contract, declared evaluator inputs and review text.
Guards run before and after adapter calls. Compilers must build a separate working
copy: changes or build output in the reviewed source snapshot fail its inventory.
One trial lock and one operator-selected shared runtime lock prevent overlapping
controller invocations. All trials targeting the same Rhino instance must use the
same runtime lock path. This does not lock out an unrelated human or MCP client.

The normal sequence is:

`probe baseline → test baseline → build → install → probe → test → probe → compare → restore → probe → test baseline → probe`

Every command has a unique request, response and log file. State transitions are
atomically replaced and fsynced before side effects. Evidence must report the
expected binary hash/MVID, exactly the frozen case names, and strict boolean
verdicts. Missing results, wrong identities and regressions reject the candidate.
A successful trial also restores the baseline; `accepted_trial` means the trial
passed, **never promotion**. Terminal runs do not repeat adapter calls.

Build failures leave the baseline installed. Once installation is pending, failures
trigger restoration followed by identity checks and the baseline suite. Failed
restoration leaves `recovery_required`, with uncertainty retained. A normal adapter
timeout kills its process group before recovery. Runtime adapters must not leave
background mutation work behind when an action returns.

After a controller crash, a pending command or recorded child requires an operator
to confirm it has stopped. The controller does not kill an old, potentially reused
PID or blindly replay installation. `--ack-child-stopped` records that attestation;
the next run rejects the interrupted trial and restores if installation may have
started. This is conservative resume/recovery, not automatic continuation of the
candidate's unfinished work.

## Local adapter protocol

The trusted adapter is an operator-owned Python file outside tracked installation
logic. The controller invokes it without a shell:

`<pinned-python> <adapter.py> <request.json> <response.json>`

Each request includes `action`, absolute trial/source/baseline/candidate/suite
paths, `suite_inputs` (absolute paths and hashes), and `expected_identity`.
The adapter writes the response JSON and exits zero only when its action finishes.
Nonzero exit status, malformed JSON or timeout is failure. stdout/stderr is logged.

| Action | Responsibility | Response |
| --- | --- | --- |
| `probe` | Observe installed bytes and the actually loaded assembly independently of the request's expected values. Check the dedicated runtime/document before mutations. | Exactly `{"sha256": "…", "mvid": "…"}` |
| `build` | Copy reviewed source to a separate build workspace, compile it, run required developer checks, put its output at `candidate_binary`. Do not install. | Actual output hash and MVID, same identity shape |
| `install` | Safely stop only the dedicated runtime, install candidate and restart/listen. Return only after completion. | JSON object; controller then independently probes |
| `test` | Execute every frozen case against the loaded runtime; save underlying reports under the trial. Do not echo expected verdicts or trust the agent's completion claim. | `{"identity": {"sha256": "…", "mvid": "…"}, "cases": {"case-name": true}}` |
| `restore` | Idempotently restore the saved baseline, even after a partial installation. Safely restart and wait until ready. | JSON object; controller then probes and retests |

The adapter must enforce dedicated-document/process ownership and preserve unrelated
user work. Machine-specific installation belongs in local instructions/adapter
configuration; the repository does not encode the app-bundle copy destination.
`probe` must distinguish a replaced on-disk file from an assembly still loaded in
memory. Installation success alone is not evidence of the loaded assembly.

`harness/trial-suite.json` defines 43 required live verdicts: 26 geometry fixtures
(each with the expected verdict twice), 11 captures, five modeling runs covering
four task types and swapped reference dimensions, and the equal-volume negative
reference control. Its evaluator/task/role inputs are pinned during preparation.
The live adapter is **not yet implemented**. These 43 cases have not been executed
as a single controller-owned Rhino trial. The file-runtime tests use two synthetic
case names and make no geometry claim.

Example once a reviewed local adapter exists (from repository root):

```sh
server/.venv/bin/python -m experiments.trial prepare \
  --repair experiments/runs/REPAIR_RUN \
  --baseline /absolute/path/to/verified-baseline.rhp \
  --baseline-mvid VERIFIED_LOADED_MVID \
  --suite experiments/harness/trial-suite.json \
  --adapter /absolute/path/to/local_adapter.py \
  --runtime-lock /absolute/path/to/shared-rhino-runtime.lock \
  --review /absolute/path/to/review.txt
server/.venv/bin/python -m experiments.trial run experiments/runs/REPAIR_RUN/trial-ID
```

The completed earlier builder pilot cannot be reused directly: its checkpoint says
it was already executed. Prepare a newly generated/reviewed candidate; do not edit
historical checkpoint flags to circumvent that gate.

## Verification and evidence

22 controller tests exercise actual subprocess calls and file replacement:
passing trial/restoration, regression, failed build, failed baseline, wrong loaded
identity, wrong evidence identity, missing cases, string verdicts, partial install,
source drift, timeout, failed restoration followed by recovery, interrupted install,
pinned-input changes, evaluator changes, manifest changes, runtime lock, blocked
builder revision, and terminal idempotence.

Final full suite: **326 passed** (103 experiment + 223 server tests).
Local records: `runs/controller-validation-20260905-final/`; JUnit report:
`runs/controller-validation-20260905-final-results.xml`. These are ignored and not
portable; rerun tests rather than assuming they exist in another checkout.

An earlier full run produced 325 passes and a transient fixture-setup inventory
failure. No unexpected entry remained when inspected. Test Git setup now disables
background auto-maintenance, and inventory errors include the offending path;
the subsequent full run passed. The initial cause was not conclusively reproduced.

## Remaining boundary and next step

The adapter, controller files and candidate are supervised trusted code. Hashes
catch drift; they are not a sandbox or proof that an adapter reports honest results.
Declared input hashes do not automatically cover every imported dependency. Review
and pin adapter dependencies, the environment and model versions for comparisons.
Current Rhino measurement runs inside the candidate process. An untrusted plugin
could interfere with its own judge; no automatic promotion is enabled.

Next: implement and review the local Rhino adapter, wire its output to the existing
live validators, and exercise a deliberately failing candidate with real restart,
restoration and independent assembly verification. Preserve all canonical tasks.
Then harden evaluator isolation and held-out comparisons. The chair screenshot pack
and baseline attempt are the next modeling track; no chair capability is claimed by
this controller milestone.
