# Workflow reorientation — 2026-09-07

The shared observer audited seven completed historical runs across five families.
Passing runs can contain failed MCP calls: the posed-body success has 27 attempts,
5 failed calls and 9 schema lookups. The alternate run fails with 64 attempts and
7 failed calls. These are heterogeneous historical observations, not an A/B result.
`historical-audit.json` preserves trace hashes, missing-value handling and verdicts.

Fresh workflow planner: `runs/workflow-plan-20260907-090526-07b1654d/`.
It proposes a new capability, batch schema discovery, rather than another modeling
recipe. The proposal passes the contract, but supervisor triage defers it: the
observed description tools belong to experimental gateways, while production tools
already expose typed MCP signatures. Measure the representative production interface
before deciding whether a batch catalog would help ordinary agents. No builder ran,
no new tool was added, and no cross-task performance improvement is claimed.

Two initial session launches hit response-schema compatibility errors (uniqueItems,
then a missing type on the status field). The adapter now submits a compatible
subset while retaining authoritative post-response validation. A third proposal
was rejected because its held-out family was absent from validation; the revised
role also disallows audit-exposed families as held-out. Failed attempts remain under
runs/workflow-plan-20260907-085911-c23b2185, ...-090114-5c69473b, and
...-090336-e4db1dbf. None are accepted proposals or plugin trials.

The immediate next milestone is a common task/session contract and a representative
MCP adapter for a small non-chair pilot, not a wholesale harness rewrite. Record
baseline agent effectiveness with native tool schemas, then investigate reliable
surface feedback using existing bounded repair infrastructure. New-file capability
builder support is a separate required extension, not a reason to postpone a
well-evidenced existing-tool repair. Keep prior task evaluators and live contracts.

Validation: the combined experiment, server and contract suites pass **474 tests**
(12 existing warnings). No Rhino build, installation or live modeling trial was
performed in this milestone; prior live evidence remains historical.
