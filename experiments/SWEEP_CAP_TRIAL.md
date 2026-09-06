# Generic sweep capping trial

Status: accepted trial (2026-09-06). Candidate passes 50/50; restoration exactly reproduces the baseline. The supervisor integrated the tested source into `harness`; the runtime remains on the restored baseline.

The chair baseline exposed open frame strips. An independent nine-fixture probe
showed that the sweep shape was correct but its two planar ends remained open.
A fresh planner proposed an explicit `cap_planar_ends` option on `sweep1`, default
false. This is a reusable capability, with no chair dimensions in production code.
The existing unused `closed` flag is a separate contract issue.

## Fresh bounded builder

A reviewed per-repair scope now replaces the capture-only path restriction for
new work. The supervisor pins a Git revision, exact existing source paths, role
instructions, requirements and development evidence. The builder has only source
read/replace tools. Its manifest is checked by hash on every access; checkout and
scope identity are checked again before review, revision and trial preparation.
Historical capture-replay instructions and scope remain supported.

The fresh builder changed exactly three files: the C# geometry handler, Python
transport wrapper and sweep command schema. The candidate validates every capped
output as a valid solid before insertion, accepts existing solids, rolls back
partial insertions and disposes temporary Breps. The supervisor reviewed the full
patch; the builder did not execute its own evaluator or install itself.

## Frozen comparison

`harness/trial-sweep-cap.json` retains all 43 original verdicts and adds seven
fixed live checks. The baseline probe measured:

| Check | Baseline |
| --- | --- |
| Omitted option leaves the original open strip | Pass |
| Explicit false leaves the original open strip | Pass |
| Capping produces the required solid with closed=false | Fail |
| Capping produces the required solid with closed=true | Fail |
| Uncapable open profile fails without document residue | Fail |
| Closed rail retains its existing solid result | Pass |
| Capping preserves the closed-rail solid | Pass |

Quarter-strip acceptance uses the previously calibrated saved-file evaluator:
validity, closure, naked edges, analytic volume/area/bounds and 192 point samples.
Saved geometry is measured twice. Failure checks compare full document geometry,
serialized attributes and layer fingerprints. Tests never change expectations
based on which binary is loaded.

The controller now distinguishes explicit measured baseline failures from
preservation checks. Candidate acceptance requires all 50 true; restoration
requires the exact baseline vector, including its three known false results.
The comparison reports improvements, regressions and unmet requirements separately.
It does not label baseline capability failures as successful modeling.

## Evidence and limits

- Builder: `runs/repair-20260906-092614-ae7792cc/`.
- Baseline focused probe: `runs/sweep-baseline-20260906-092845/`.
- Active trial: `runs/repair-20260906-092614-ae7792cc/trial-667b3692/`.
- First launch attempt `trial-194a32ba` stopped before build/install because the
  adapter needed an absolute repository PYTHONPATH; it was safely rejected before
  a new trial. The fresh document must also be explicitly claimed by the supervisor.
- Source validation: four transport cases and eight schema cases passed. A
  supervisor import initially created a cache file in the candidate; the integrity
  gate rejected that extra file. The generated file was removed and the source
  validator now avoids writing import bytecode into the reviewed checkout.
- The saved 65-object chair and its original SHA-256 were verified before restart;
  all geometry, serialized attributes and layers matched the previous fingerprint.
  Rhino's close operation was slow but ultimately exited normally. No forced
  termination was needed and no loaded binary was replaced.
- Desktop lifecycle is supervised. No forced AddBrep insertion failure, multi-result
  cap failure or non-planar boundary fixture is claimed. The open-profile fixture
  verifies one realistic uncapable case. Closed-rail checks establish preservation
  for one circular rail, not all possible sweep frames.
- This does not establish improved chair reconstruction or generalization to
  unseen objects. Those require fresh modeling and transfer tasks.

## Candidate measurements

Both cap-enabled quarter-strip outputs are valid solids with zero naked edges,
volume 31415.92308169094 mm³ and area 9824.777097622773 mm². The default stays
open, with eight naked edges and area 9424.777097622773 mm². The uncapable profile
returns an explicit capping failure and the complete document fingerprint is
unchanged. All seven sweep artifacts/behaviors meet the frozen requirements;
all 43 historical verdicts pass, including five fresh modeling sessions.

Baseline source revision: `4af72cde8db7a7794ae09991255526decd29168c`.
The exact builder patch is retained at `harness/repairs/sweep-cap.patch`, SHA-256
`46b77d5c4c55f6ae5ef186f2a781040e8d6816d304edd977cc44eca7dacb4ce7`.
Candidate binary MVID: `79b1500e-e20d-47af-9c83-6f915729a712`; SHA-256
`635e8ccf94a55775ea2b58166d83eb995ad517c3de3d66963caed7772a027d7e`.
Original binary MVID: `90d87782-2887-435e-a8b2-02467f0c5094`; SHA-256
`ac4699e049474f41adcae08a6b8226eb84a65de573e1de82bf238ebeb8491a35`.

The next modeling milestone is a fresh agent building a capped curved strip
through its normal permitted MCP tools, with objective saved-file evaluation,
then a different geometry/pose to begin checking transfer. The scripted probe
above demonstrates the tool capability; it does not substitute for that fresh
modeling test. Hierarchical layers and continuous cushions remain separate work.

## Completed restoration and source adoption

Restoration report `trial-667b3692/live-512dd126/result.json` exactly matches the
initial `live-cfadef63/result.json` case vector: 47 true, with the same three
explicit capability failures. Candidate report `live-035ab7b3/result.json` has
50 true. Controller state is `accepted_trial`, `runtime_dirty=false`,
`promoted=false`. Fifteen fresh modeler sessions ran across the three suite passes.

After completion the supervisor integrated the exact reviewed three-file patch
into the branch and added permanent transport/schema checks. This manual source
adoption does not change the trial's runtime-restoration policy. Rhino is left on
the original plugin in an empty dedicated document (PID 59985 at handoff).
The next modeling milestone must explicitly install/pin the verified capping
version before advertising or using its new option.

Final source checks: **385 passed** (144 harness, 228 server, 13 contracts).
Standalone schema validation, experiment lint/format and server source lint pass.
The new schema test was adjusted to avoid adding a return-value warning; its
focused rerun passes. Historical contract functions still use boolean returns.
A fresh post-trial planner returned `accept`, preserving the distinction between
source adoption, fresh-agent modeling and runtime promotion; its evidence and
recommendation are saved as `post-trial-evidence.json` and `post-trial-plan.json`.
