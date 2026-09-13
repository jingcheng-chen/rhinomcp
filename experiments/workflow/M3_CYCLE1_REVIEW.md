# M3 cycle 1: reviewed attribute overload repair

The fresh planner proposal is in `m3-cycle1-proposal.json`; the bounded builder
ran in `repair-20260910-084145-b8aad755`. The first builder candidate failed independent user-string preservation and was
rejected before agent comparison. A fresh revision in
`repair-20260910-085059-a4317332` also edits a detached attributes duplicate.
Supervisor source review accepts these two handler changes:
`property.Value.ToString(Formatting.None, Array.Empty<JsonConverter>())` replacing
the single-argument call in `ObjectAttributes.cs`, and
`var attrs = obj.Attributes.Duplicate()`. Loaded-assembly reflection
confirms Rhino's JToken has the two-argument signature. No dependency/schema/other
behavior change is included. The planner's array/object encoding wording is
corrected: the existing contract rejects those values and continues to do so.

Independent validation: preserve saved object identity/geometry; exercise layer,
name, color, scalar strings/numbers/booleans, null/deletion/clear, visibility, lock,
material inheritance and invalid input. Seven saved rectangle-curve fixtures
calibrate the new held-out evaluator before agents see that family. The shared
scene evaluator and full-catalog binary comparator are extended and frozen before
comparison. No construction recipe is supplied to agents or the builder.

Comparison: released 0.4.0 versus the two-line candidate, identical full production
catalog, gpt-5.6-terra medium, 50 calls and 240 seconds per session. Two pairs per
family in AB/BA order: small assembly, recovery, held-out planar curve editing.
Artifacts from both arms are judged after restoring the trusted released binary.

Keep only if the comparison finishes with baseline restored, candidate passes all
six saved-file tasks (including both held-out attempts), has no per-family
correctness regression or increase in failed calls, and shows benefit under
`correctness_then_calls_v1` in at least one discovery family. Otherwise reject or
record incomplete evidence. Time/tokens are secondary; two repeats are descriptive,
not statistical proof. A kept change becomes a versioned PR; do not auto-merge,
publish or change the selected production baseline.

Before comparison, the auditor was corrected to recognize a bare {"error": ...}
result as a failed call. M2's original audit missed three get_object_info failures;
raw traces and task verdicts are unchanged. Re-audited M2: 104 calls, 19 failures.
This is an instrument correction made before freezing this comparison, not an
adjustment to favor the candidate. It also supplies evidence for a later, separate
cycle about object-lookup parameter wording/error propagation.
