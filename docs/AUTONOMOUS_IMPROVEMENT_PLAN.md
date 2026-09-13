# RhinoMCP autonomous improvement plan

Current direction (2026-09-09): enhance the overall Rhino modeling workflow by
detecting flaws in agent runs and improving the MCP tools. Modeling output is
evidence, not the product; precision beyond a task's realistic tolerance and any
single object (the chair) are out of scope. The baseline is the released 0.4.0.
See [the operating brief](../experiments/CONTINUE.md) for the milestone queue and
[the governing workflow](../experiments/workflow/README.md) for the cycle, tolerance
policy and implemented machinery. Phases 1 to 5 below are historical design context;
the roadmap from 0.4.0 and the Grasshopper phase follow them.

## Objective

Improve MCP capabilities, feedback and reusable workflows, measuring task success,
tool failures, call count, duration, tokens and recovery across a diverse suite.
Support new tools and interface improvements as well as defect repairs. Keep agent
model, task input, evaluator, environment and budget fixed across plugin comparisons.
Require validation outside the task family that motivated a change. New test counts
and a better single model do not establish general improvement.

## Existing foundation

- `analyze_objects` exposes validity, bounding dimensions, and type-specific geometry measurements.
- `measure_objects` exposes pairwise relationships, with explicitly approximate bounding-box fallbacks. Those fallbacks must not establish exact geometric acceptance.
- `capture_viewport` supports named views and image capture. Fixed framing still needs verification; automatic zoom must not conceal scale errors. Captures can change camera state.
- Python integration tests currently use a mock Rhino server. They validate transport behavior, not actual Rhino geometry.
- Protocol changes require synchronized Python wrappers, C# handlers, command schemas, and envelope coverage under repository guidelines.

## Phase 1: Establish a trustworthy live evaluator

Create a task definition with an ID, units, document tolerance, starting document, modeling instructions, allowed tools, budgets, output selection rules, and explicit acceptance predicates. Keep reference geometry and evaluator rules outside the builder's writable workspace and outside the modeling agent's accessible inputs.

Start with five development tasks:

1. Create a box with specified dimensions and volume.
2. Move and rotate an asymmetric object to a specified pose.
3. Subtract a through-hole from a solid and verify the hole location and remaining volume.
4. Create a closed profile and extrude it into a valid solid.
5. Reconstruct a simple stepped object from reference-generated orthographic images, with units and one scale dimension supplied.

Add held-out variants with different dimensions and arrangements. Detailed held-out feedback must not enter the repair loop; repeated tuning against those results would turn them into development tasks.

Implement deterministic checks using trusted RhinoCommon evaluation code where possible. Save the candidate document, then evaluate a copy with the builder stopped. Bind results to the saved artifact hash. Missing objects, unsupported measurements, and evaluator failures must never silently pass. Check the complete output set so that extra geometry cannot be hidden by selecting only a correct subset.

Validate the evaluator with known-correct models and deliberately incorrect variants: wrong scale, wrong pose, missing holes, extra geometry, and open solids. Prefer independent analytic expectations for simple shapes over evaluating a plugin function with itself.

Exit criteria: correct fixtures pass; all deliberately incorrect fixtures fail the appropriate checks; repeated evaluation of identical geometry gives the same verdict within declared tolerances. A live end-to-end run saves a document and produces a machine-readable report.

## Phase 2: Add bounded task execution and evidence

Build a Python orchestration package under a proposed `experiments/` directory, outside the production request path. Use the current MCP interface for the modeling agent. Record agent model/settings, prompt and tool versions, source revision, loaded plugin identity, task version, units, tolerance, tool calls/responses, elapsed time, and final artifacts.

### Agent client and session lifecycle

Use a deterministic Python controller to launch and supervise agent sessions. Start with a Codex CLI adapter using non-interactive execution, event logging, and schema-constrained final outputs. Keep the adapter replaceable so a Claude Code adapter can be added after verifying its execution, permissions, MCP configuration, output, and recovery capabilities. Do not require visible desktop tasks or UI automation to run the experiment.

The adapter accepts a role, prepared input manifest, working directory, client/model settings, permission profile, MCP configuration, output schema, and budget. It returns a session identifier when available, process status, event-log paths, usage when available, and the final structured result. Record client versions and supported controls; reject a role configuration if its required isolation cannot be enforced. Hold the selected client/model configuration fixed during an experiment rather than silently switching providers after a failure.

Launch a fresh session for each role invocation and each new modeling attempt. Transfer progress through versioned files and evidence, not by inheriting the previous role's conversation. Resume only unfinished work within the same role, using an explicit saved session ID and unchanged authorized scope. If those conditions cannot be established, start a fresh session from the last verified checkpoint. A new conversation alone does not enforce filesystem or MCP isolation.

The controller must:

- Prepare the role's input manifest and enforce its accessible files, writable paths, and tools. Protect the controller, evaluator, reference answers, and acceptance thresholds from agent modification.
- Record experiment, cycle, task, attempt, role, and session IDs together with input hashes and output artifact identities.
- Track pending, running, completed, failed, timed-out, and interrupted stages. Advance only after validating required outputs and recording a durable checkpoint.
- Enforce per-stage time limits and configured resource budgets, capture execution events, and terminate timed-out work before starting another writer.
- Apply bounded retries for malformed outputs and infrastructure failures. Retain failed-attempt records and partial artifacts; do not silently retry geometry failures until one passes.
- Reconcile saved checkpoints with actual files and Rhino state after interruption. Never blindly replay a tool call that may already have changed the document.

Agent sessions and the Rhino application session have separate lifecycles. Enforce exclusive access to the dedicated Rhino document for modeling, capture, evaluation, reset, and plugin installation. Stop the current writer and save its artifact before evaluation; operate on a copy when capture changes camera state. Filesystem permissions alone do not restrict MCP side effects: enforce tool access at the connection or execution boundary, including arbitrary-code tools.

Use a dedicated Rhino evaluation session with a fresh document per attempt. Run tasks serially against that session. Set per-task time and tool-call limits; classify crashes, connection failures, and timeouts separately from geometry failures. Never reset an unrelated user document.

Reports distinguish `pass`, `fail`, and `inconclusive`, and retain individual measurements rather than relying only on a combined score. A task passes only when every mandatory predicate passes. Save rendered views with fixed projection, framing, and display settings for supplementary inspection.

Exit criteria: all five tasks can run unattended with isolated documents, bounded execution, complete reports, and recoverable failure handling. Demonstrate session launch, validated output collection, timeout handling, and recovery from a checkpoint without duplicate document mutations.

## Phase 3: Close the planning and repair loop

Use sequential roles:

- Modeling agent: produces a Rhino artifact using the permitted MCP tools.
- Evaluator: measures the frozen artifact using protected criteria.
- Optional QA reviewer: independently interprets screenshots and execution evidence. Its observations supplement deterministic checks and cannot override a failed or inconclusive mandatory predicate.
- Planner: reads development-task evidence and classifies the failure as modeling strategy, tool implementation, missing capability, environment, or ambiguous requirement.
- Builder: makes one bounded code or guidance change for a reproducible failure.
- Validator: runs relevant repository checks and compares baseline and candidate on live tasks.

The planner outputs a failure reproduction, proposed scope, expected observable improvement, and behavior that must be preserved. Uncertain diagnoses get an experiment rather than an immediate plugin modification. Each attempt persists a concise report and evidence index so later rounds can retrieve relevant history.

### Session handoffs and role boundaries

| Stage | Inputs | Authority | Required output |
| --- | --- | --- | --- |
| Modeler session | Public task, reference pictures, permitted tool guidance, starting document | Modify the dedicated modeling document through allowed tools; no plugin source edits or hidden references | Candidate document identity, execution record, completion claims, unresolved problems |
| Deterministic evaluator | Frozen candidate and protected evaluation specification | Trusted evaluation process; no agent session required | Predicate results, measurements, evidence paths, evaluation status |
| Optional QA session | Public requirements, frozen candidate observations, shareable measurements | Inspect an evaluation copy through restricted tools; no candidate edits or hidden benchmark material | Observations with evidence references and explicitly stated uncertainty |
| Planner session | Public requirements, current project state, development-task findings, concise history index | Read project and permitted evidence; write only its plan | Diagnosis, bounded objective, expected behavior, preservation constraints, validation requirements |
| Builder session | Validated plan, current plugin checkout, relevant development evidence | Edit the candidate checkout and run developer checks; no evaluator or reference modifications | Candidate revision or patch identity, change summary, test evidence, remaining gaps |
| Validator | Candidate revision, repository checks, protected task suite | Controller-owned checks and isolated live evaluation | Baseline/candidate comparison and acceptance or rejection evidence |

Require schemas for agent outputs and validate referenced artifacts before each handoff. Malformed output triggers only a bounded correction attempt; an agent's successful exit or completion claim does not establish task success. Hand off a concise summary and categorized evidence index, exposing detailed records only when relevant and authorized. Keep hidden evaluation material and held-out feedback out of all agent sessions.

The builder reproduces the issue and establishes a baseline before editing, then runs focused checks after meaningful changes before independent validation. The planner also tracks unmet capabilities and can propose a small, verifiable feature increment when warranted, balancing repair with capability growth. Do not require an unrelated new feature during every repair cycle.

The first loop runs a modeling task and gathers evidence. Later loops use a fresh planner session to select a modeling-strategy revision, a plugin repair, or a capability increment. Plugin changes proceed through a fresh builder session and validation before new modeler sessions exercise the candidate. Strategy-only experiments keep the plugin version fixed. No agent is responsible for launching or policing its own independent evaluator.

Freeze agent settings and task budgets during baseline/candidate comparison. For stochastic modeling tasks, repeat matched baseline and candidate attempts using a repetition count and decision rule established before comparing results. Keep code and guidance changes separate initially.

Exit criteria: demonstrate one actual failure, a supported diagnosis, a bounded change, and measured improvement without failed preservation checks. Verify that role transitions create fresh sessions with only authorized handoff inputs, and that builder access to protected evaluation files and tools is denied. If no suitable failure appears, report that result rather than inventing a change.

## Phase 4: Automate candidate installation and selection

First verify Rhino plugin loading behavior locally. Do not assume a running Rhino process can reload a replaced assembly. A successful build or file copy is insufficient: confirm the loaded candidate identity and an MCP handshake before testing.

Run Python tests, schema validation, lint/format checks, and the C# build as appropriate to the change. Follow the repository's local app-bundle copy instruction when building for local validation; do not put that machine-specific copy behavior in tracked automation. If process restart is required, make it part of the dedicated evaluation session lifecycle.

Automatically select a candidate as the next experimental baseline only if required checks pass, it meets the predeclared improvement rule, and preservation tasks do not regress. Track held-out results separately. Retain the previous verified binary and source revision for rollback. Selection as an experimental baseline does not publish a release or merge changes into the main branch.

Set a maximum cycle count and resource budget. Stop on repeated lack of improvement, unresolved environment failure, exhausted budget, or ambiguous acceptance criteria. Preserve the best verified candidate rather than assuming the last attempt is best.

Exit criteria: load a candidate, verify its identity, evaluate it, reject a deliberately regressing candidate, and restore the previous verified version without manual session repair.

## Phase 5: Expand visual reconstruction

Generate images from hidden reference models using recorded camera parameters. Compare multi-view silhouettes and sampled surface distances, with predefined units, alignment rules, and tolerances. Allow equivalent valid surface constructions. Gate geometry validity separately from visual similarity.

Introduce real photographs only after the controlled suite works. Record what is known about scale and cameras and which hidden geometry is unspecified. Treat AI visual critique as supplementary feedback; it cannot turn an ambiguous task into an objective pass.

## First implementation milestone

Deliver Phase 1: task/report formats, five small fixtures, trusted geometry checks, evaluator validation, and one recorded live Rhino run. This establishes whether the feedback is reliable enough to drive autonomous repairs before investing in agent orchestration or automatic deployment.

## Roadmap from 0.4.0 (2026-09-09)

Phases 1 to 3 are complete, phase 4 is supervised rather than unattended, and phase
5's photo track is set aside. The queue continues in [CONTINUE.md](../experiments/CONTINUE.md):

| Milestone | Outcome |
| --- | --- |
| M0 Re-baseline | `current-baseline.json` points at the released 0.4.0; active tasks carry realistic tolerances |
| M1 Flaw detection | One command turns run traces into a ranked flaw report under a fixed taxonomy |
| M2 Realistic families | Editing, pipeline, assembly, inspection and recovery tasks with calibrated evaluators |
| M3 Improvement cycles | Proposal, bounded change, comparison and keep/reject per top-ranked flaw; kept changes ship via PR |
| M4 Held-out bank | Sealed families spent one per validation and replaced |
| M5 Unattended operation | Fresh Parallels VM (decided 2026-09-10, deferred until a setup exists): feasibility spike, guest lifecycle, trusted-judge separation, denial tests, then unattended acceptance |
| M6 Grasshopper harness | Same cycle over the `gh_*` tools |

## Phase 6: Grasshopper harness

Apply the same loop to Grasshopper once the Rhino queue has produced a kept
improvement. Tasks are text descriptions of small definitions with checkable outputs
(a parametric grid driven by an attractor, a loft from sliders, sections through a
solid). The modeler gets the `gh_*` command family only and starts every attempt from
`gh_create_document`. The evaluator reads the graph (`gh_get_graph`,
`gh_get_document_info`), runs it (`gh_run_solution`) and checks output parameters
(`gh_get_parameter_value`) against declared expectations; previews from
`gh_capture_preview` are supplementary. Deterministic predicates: the solution runs
without errors, required components and connections exist, there are no orphan
components, and outputs are within tolerance. A bake-to-document command is a likely
first capability proposal so the saved-file evaluators can judge resulting geometry.
The flaw taxonomy gains component search churn, wrong parameter names or indices,
wiring errors, expire/run loops and layout thrash. Orchestration, audit and comparison
code are reused; only a Grasshopper task type and evaluator adapter are new.
