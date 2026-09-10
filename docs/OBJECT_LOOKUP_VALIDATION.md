# Object lookup description validation

`get_object_info` previously advertised `object_name`, while its signature and
command parameters accept `id` or `name`. Two earlier full-catalog inspection calls
followed that wording and failed. The description now uses the accepted selectors,
requires at least one, states ID precedence, and points to `get_objects` when no
selector is known. Executable code, schemas, annotations and responses are unchanged.

Independent review of the fresh bounded builder's candidate verified identical
executable AST and all 70 tool definitions identical except this description.
All 285 server tests pass against that candidate source.

## Frozen comparison — 2026-09-10

Two fresh AB/BA pairs per family used released 0.4.0 for both binary arms, separate
baseline/candidate Python sources, the full 70-definition catalog, gpt-5.6-terra
medium, 50 calls and 240 seconds per session. Section extraction was held out of
discovery and builder context. Eight saved controls calibrated its evaluator.
All twelve saved outputs passed independent evaluation under baseline code after
candidate sessions stopped; every task restored its original document fingerprint.

| Family | Median calls, baseline → candidate | Failed calls, baseline → candidate |
| --- | --- | --- |
| Inspection | 4.5 → 3.5 | 0 → 0 |
| Editing existing geometry | 12 → 11.5 | 1 → 1 |
| Held-out section extraction | 20 → 14 | 3 → 0 |

The candidate meets the predeclared rule: all six candidate outputs pass, no
per-family correctness regression or failed-call increase, and lower calls in a
discovery family. Two repeats are descriptive evidence, not statistical proof.
The original wrong-field error did not recur in either arm, so this does not
establish that the wording caused every observed call saving. Inspection wall time
was slightly higher for the candidate; timing was a secondary observation.

Local harness evidence: `workflow-binary-20260910-093344-5aa4136d`; bounded builder
`repair-20260910-092552-3c39fc7d`. The comparison excluded the separate attribute
repair. The prepared release branch includes that repair from PR #53, uses its
unchanged verified 0.4.1 plugin build, and passes the combined server tests; no joint
agent-performance claim is made. Both changes target the same unreleased 0.4.1.

To inspect the correction, list MCP tools and compare the `get_object_info`
description with its `id` and `name` input fields. Read-only calls with either
selector continue to work, and supplying both continues to use `id`.
