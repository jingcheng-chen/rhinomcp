# Bounded reviewed comparison campaigns

`experiments.campaign` executes a finite queue of already reviewed/prepared binary
comparisons. Every entry must share the same baseline, agent settings, task suite,
acceptance rule and deferred trusted-baseline judge. A candidate proposal does not
authorize queue entry. The campaign itself never builds or installs source changes.
Its child comparator uses the existing supervised binary lifecycle.

A frozen manifest specifies the queue, aggregate session/call/time limits and a
maximum number of unsuccessful comparisons. The controller reserves enough remaining
allowance for the next comparison's full declared limits before dispatch. Actual
usage is recomputed from every completed child session. Missing or inconsistent
usage blocks further dispatch. Observed overruns are recorded without clamping.
The queue stops on exhaustion, no benefit, insufficient resources, failure, uncertain
state, changed evidence, or the first positive comparison requiring selection review.
A positive comparison is not permission to promote; the independent selection gate
still requires its preservation trial and scoped reserved-case evidence.

Dispatch intent is persisted before creating the child process. After parent process
loss, a completed child is accounted without rerunning it. An incomplete child must
be restored/inspected, and may use verified comparison continuation if eligible.
Completed evidence is hashed before advancing the queue. It is never silently
reinterpreted after source changes. Failures retain logs and the active child index.

The JSON preparation input has `comparisons` (absolute prepared run paths), `limits`
(`sessions`, `tool_attempts`, `model_seconds`), positive `max_no_benefit`, and `review`.
Use `python -m experiments.campaign prepare CONTRACT`, then `run DIRECTORY`.
`status` is read-only; `reconcile` accounts a completed active child without dispatch.

Ten tests cover ordered dispatch, stop conditions, interruption reconciliation,
no replay, wrong baselines, altered evidence, resource accounting and child failure.
Live two-candidate campaign validation is complete: eight fresh posed-prism models
all pass, neither diagnostic candidate establishes benefit, and the queue stops at
exhaustion. Actual usage is 49 attempts and 247.55 modeling seconds. Four supervised
binary transitions and the verified document handoff pass. The selected planar
baseline is restored. See `campaign-results.json`; source snapshots and all evidence
are retained in `runs/campaign-20260908-222059-6176f1bc`. This is a bounded reviewed
queue, not autonomous proposal approval, adversarial isolation or unattended desktop
installation. Provider costs are not a hard billing cap.
