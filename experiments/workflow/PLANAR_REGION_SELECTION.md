# Scoped selection review: create_planar_region

Select the reviewed six-file planar-region capability for the experimental baseline.
The frozen capability trial passes all 79 candidate requirements, preserves the 61
existing requirements and restores the exact original baseline. The twelve-session
native comparison is complete, with all models judged after trusted-baseline restoration.

Both baseline runs fail on each trimmed task; both candidate runs pass on each task,
including the reserved patch. Candidate median attempts are 11 for each patch,
versus baseline medians 15.5 and 25.5. Correctness improvement is the primary result.
The through-hole task passes twice on both versions with seven median attempts;
its candidate median time is slower (39.9 versus 31.0 seconds), so no efficiency
improvement is claimed there. Total observed usage is 154 attempts and 908.55 modeling
seconds across twelve sessions, within the frozen limits.

This supports a scoped typed planar-region capability, with reserved-case validation
and another family's preservation. It does not establish broad unseen-family transfer,
statistical significance, immutable backend model weights or adversarial judge isolation.
The unrelated bounds repair remains unselected because its workflow comparison regressed.

Use the source journal to apply exactly the reviewed additions and protocol coverage,
verify runtime activation through the existing supervised lifecycle, then exercise
rollback of both source and binary. Reactivate the same reviewed selection only after
rollback restores the previous files and runtime. Keep completed comparison and trial
records immutable; retain the selection and rollback receipts separately.

## Executed outcome

Source and runtime selection, rollback and reactivation all passed. The full native
catalog changed 68→69→68→69 with every prior definition unchanged. The selected six
production files are committed locally as `22ffe046f42b96a58aff8dd56f6eb06080f2bc7e`;
no push occurred. Runtime MVID is `f2c73913-0e83-4d95-9eb5-273420f8ca70`.
The separate journal is `runs/selection-20260908-214357-b9bfc9f6`, with activation,
rollback and reactivation verification receipts. See `planar-region-selection.json`
and `current-baseline.json`. Subsequent controller tests restore this selected baseline.
