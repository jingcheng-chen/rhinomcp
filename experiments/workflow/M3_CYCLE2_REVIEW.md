# M3 cycle 2: reviewed lookup description repair

The fresh planner `workflow-plan-20260910-092309-4abbe5be` proposes correcting
get_object_info selector wording. The fresh bounded builder
`repair-20260910-092552-3c39fc7d` changes only that function's docstring. Independent
review confirms identical executable AST, all 70 tool definitions unchanged except
get_object_info.description, and unchanged selector behavior. This does not include
the cycle 1 attribute repair or change the bare-error return contract.

A prior checkout preparation stopped before builder dispatch when Git's transient
maintenance lock changed during inventory. That failure is retained; the fresh
preparation disabled Git auto-maintenance for that process only. It is not a
replayed builder or modeler attempt.

Comparison: released 0.4.0 Python and plugin versus the description candidate on
the same released binary. The shared binary comparator accepts source-only trials
only with an explicitly declared description intervention, full catalog, equal
binary identities, no added tools, and exact catalog equality outside declared
descriptions. Whole source hashes are frozen. Each task uses a fresh Python MCP
server from its arm's source and a fresh gpt-5.6-terra medium session.

Two AB/BA pairs per family: document inspection, editing existing geometry, and
held-out section extraction. Full 70-definition catalog, 50 calls, 240 seconds;
identical task/evaluator/environment per arm. The section parameters were declared
after the planner and never supplied to the builder. Eight saved-file controls
calibrate correct output, bounds, curve height, count, layer, units and identity.
All 12 artifacts are judged under baseline code after candidate sessions stop.

Keep only if complete with clean verified baseline, all six candidate saved tasks
pass (including both held-out cases), no family has a correctness regression or
increase in failed calls, and correctness_then_calls_v1 shows benefit in at least
one of the two discovery families. Otherwise reject; do not rerun until passing.
Two repeats are descriptive evidence, not statistical proof. Time/tokens are
secondary. A kept change needs a separately reviewed versioned PR; no automatic
promotion, merge, release or production baseline change.
