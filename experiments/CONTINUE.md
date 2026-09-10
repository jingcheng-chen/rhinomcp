# Continue autonomous RhinoMCP improvement

Entry point for a fresh development session (Codex CLI or Claude Code) with no
chat context. Last updated 2026-09-10 evening, after M0b, M3b and M6 and the review of
their verdicts; the VM is decided but deferred. Verify repository
and application state before acting; nothing below about running processes, open
documents or loaded plugins is an assumption you may keep.

## Direction — user clarification, 2026-09-09

Improve the overall modeling workflow in Rhino through MCP: run fresh agents on
realistic modeling tasks, detect the flaws in those runs, and change the MCP tools
(behavior, responses, descriptions, guidance, new capabilities) so that the next
agents do better across tasks. Modeling output is evidence; it is not the product.

- **Not the aim:** modeling anything super precisely. Sub-millimetre surface
  fidelity and construction recipes for one shape (the 2026-09-09 biquadratic
  recipe, the 0.05 mm panel tolerance) are out of scope unless a tool misled the
  agent. A result that is valid, correctly posed and roughly right but misses a
  tight tolerance is a fidelity note, not a workflow flaw.
- **Not the aim:** the Barcelona chair or any single object. Chair and cushion work
  is archived evidence only.
- **A flaw is** anything in a run that a better tool would have prevented: failed
  or retried calls, misleading or incomplete responses, schema confusion, many
  calls for one intent, workarounds through scripting or `run_command`, wrong
  defaults, anchors or pivots, missing capabilities, poor recovery after a mistake,
  and completion claims the evaluator rejects.
- **Later:** the same harness for Grasshopper (milestone M6 below).

This supersedes the precision-oriented next steps in [HANDOFF_HISTORY.md](HANDOFF_HISTORY.md).

## How to work

1. Read, in order: repository `AGENTS.md`; this file; [workflow/README.md](workflow/README.md)
   (the cycle, tolerance policy and implemented machinery); [harness/README.md](harness/README.md)
   (map of code and permissions); [README.md](README.md) here (run commands). Open
   `HANDOFF_HISTORY.md` only for the provenance of a specific run or decision.
2. Verify state before anything live: `git status`, `git log -5`, the installed
   server (`server/.venv/bin/python -c "import rhinomcp; print(rhinomcp.__version__)"`),
   and the loaded plugin through the `describe_capabilities` tool, which reports
   `version`, `server_version` and `update_advice`. Never assume a Rhino document,
   process or controller from a previous session.
3. Work in bounded cycles on the `harness` branch: one milestone step, tests green,
   one coherent commit whose message states what was verified. Product changes
   (`server/`, `plugin/`, `contracts/`) reach users only through a PR to `main` and
   a GitHub release, with the version bumped in `server/pyproject.toml`,
   `plugin/manifest.yml` and `plugin/rhinomcp.csproj`, and `CHANGELOG.md` updated.
4. Evidence discipline is unchanged: fresh sessions at role boundaries; independent
   saved-file verdicts; agent completion claims never count; failures are retained,
   never rerun until one passes; pins (source hashes, plugin identity, agent model
   and effort, task versions) recorded before comparing; one intervention at a time;
   held-out families declared before use and never tuned against.
5. Tolerances describe realistic modeling needs and are fixed before a run. Never
   loosen one to pass a run or tighten one to manufacture a flaw; re-declare the task
   as a new version instead. The policy is in `workflow/README.md`.
6. Ask the user only for: logins and licenses that must be entered by a person
   (the guest's Rhino account, the guest's Codex login, Parallels prompts); any
   change to a released tool's wire contract that would break older clients or
   plugins; and anything touching user documents or the installed Rhino outside the
   dedicated test session. The isolation environment is decided (Parallels VM) but deferred: do not start
   M5 without an explicit go from the user. Decide and record everything else yourself.
7. Before every commit: from `server/`, `.venv/bin/python -m pytest` (285 at last
   count) and `.venv/bin/ruff check src/rhinomcp`; from the repository root,
   `server/.venv/bin/python -m pytest experiments/tests` (471) and
   `server/.venv/bin/python -m pytest contracts/test_schemas.py` (13); for plugin
   changes, `dotnet build plugin/rhinomcp.sln --configuration Release`.

Do not: build object-specific runners; resume chair or cushion work; add
construction recipes to guidance without a cross-task flaw that motivates them;
promote a candidate automatically; leave a controller or agent running; paste
credentials anywhere; reinstall the plugin into a Rhino that holds user work; touch,
clone or boot the user's personal `Windows 11.pvm`.

## Current state — 2026-09-10, evening

- Released: 0.4.1 (`releases/0.4.1`). Runtime baseline: Package Manager 0.4.1,
  MVID `2c401408-5a49-4a4b-831d-fa9f5cb913c5`, SHA256 in
  `workflow/current-baseline.json`; server and plugin both 0.4.1, no update advice.
  `harness` includes `main` up to that release. Production source is unchanged since;
  no candidate is adopted.
- Complete: M0 to M4, M0b, M3b and M6. M5 is deferred by the user; do not start it.
  Reports: `workflow/REBASELINE_041.md`, `workflow/M3B.md`, `workflow/GRASSHOPPER.md`,
  and the M1 to M4 reports listed under Pointers.
- Latest observations on 0.4.1: nine release and scene runs, eight pass; the v2 panel
  (0.5 mm shape tolerance) still fails bounds and boundary while the agent claims
  completion. Three Grasshopper discovery runs pass with zero failed calls.
- Three improvement cycles ran on 0.4.1 (two Rhino wording changes, one Grasshopper
  wording change); all were rejected. In each, most failed calls were the gateway's
  own refusals (execution tools; Grasshopper components outside a 35-item allowlist),
  and the remaining differences were within noise at two pairs per task. Those
  verdicts measured the guard, not the candidates. Keep rule v2 (M3c) corrects that.
  Do not reopen the closed trials or reuse their held-out cases as unseen.
- Recorded behavior defects not yet acted on, the M3c targets: `gh_get_parameter_value`
  and `gh_set_parameter_value` ignore `output_name` and `input_name` because the
  Python wrapper also sends a default index that takes precedence in C#
  (`workflow/gh-selector-observation.json`); `gh_build_graph` value targets confuse
  both agents; assigning to a non-existent layer fails with an error that names no
  existing layer; the SURFACE path still yields off-bounds panels.
- Held-out bank: joining, directional projection and vector frame are spent and
  closed; sealed and unopened: instance/block reuse, mesh connectivity repair,
  pattern filtering. See `workflow/HELD_OUT.md`.
- Gateway: execution tools are refused and recorded in full-catalog runs; Grasshopper
  runs own a fresh GH document per attempt and must start with `gh_create_document`.
- Agents: the Codex adapter (default, comparisons) and the Claude adapter (fixed
  cross-agent checks).
- Hygiene debts: absolute `/Users/chen` paths in new audit JSON, 3.9 MB of evidence
  added per day, one-line commit messages. Rules in M3c.
- Tests at last verification: 285 server, 519 experiments, 13 contracts; ruff passes.

## Milestones from here, in order

Order as of 2026-09-10, evening: **M3c**, then the next Grasshopper cycle under keep
rule v2. M5 is deferred by the user and stays parked until an explicit go. Each milestone ends with tests green, a portable
report under `workflow/`, the state section above updated, and a commit.

### M0 — Re-baseline on the released 0.4.0 (complete, 2026-09-09)

- Build the plugin from tag `releases/0.4.0`, or install it from the Package Manager
  into the dedicated Rhino; restart Rhino; record the loaded identity (MVID, SHA256)
  and server 0.4.0 in `workflow/current-baseline.json` through the existing selection
  flow. Move the pre-release entries into history.
- Re-declare the panel and trimmed-patch tasks under the tolerance policy as new
  task versions (`*_v2.json` or a `version` field); keep the old files for
  historical pins. Retire `unseen_precision_panel.json` from the active suite.
- Re-run the native pilot once per family on 0.4.0 to refresh baseline observations.

Done when `current-baseline.json` points at 0.4.0, every active task states a
realistic tolerance, and one fresh baseline run per family is recorded.

### M1 — Flaw detection from traces (complete, 2026-09-09)

Turn `workflow/audit.py` into a flaw report. For each run, classify friction into a
fixed taxonomy and count it: failed calls and their causes; retries after an error;
schema or discovery calls; redundant reads of the same thing; calls per required
operation; `run_command` or script fallbacks where a typed tool exists; misleading
responses (a success the evaluator later contradicts, or one the agent misread);
wrong anchors, pivots or defaults; recovery loops (undo, delete, recreate); and
unmet capability (the agent says a tool is missing). Aggregate across runs by tool
and by family, ranked by frequency times cost in calls and seconds. Validate the
classifier on the traces registered in `historical.json` and the 2026-09-09 runs.
Write `workflow/FLAW_TAXONOMY.md`.

Done when one command produces a ranked flaw report from a set of runs, with tests,
and the top three flaws on current traces are named with evidence.

### M2 — Realistic workflow families (complete, 2026-09-10)

Add task families that reflect how people model in Rhino, each with a saved-file
evaluator at realistic tolerances, and where useful a starting-document variant:

- editing existing geometry: move, scale or rotate a given object to a target;
  offset or fillet a given curve; change layers or attributes of existing objects;
- curve → surface → solid pipelines: profile, loft/sweep/extrude, cap, boolean;
- small assemblies with layers and names, for example a table top with four legs;
- inspection on a prepared document: find, measure, report, without mutation;
- recovery: a wrong intermediate result must be undone or deleted correctly.

Run fresh agents with the full production catalog as well as the native subset, so
tool choice in the wild is observed; a fallback to scripting is a flaw signal, not
a gateway artifact. Reuse `pilot.py`, `runner.py` and the evaluator registry; do not
fork orchestration. Declare which families are held out before running discovery.

Done when at least four new families are registered, calibrated with correct and
flawed fixtures, and have a fresh baseline run on 0.4.0.

### M3 — One improvement cycle per flaw (complete, 2026-09-10)

For the top-ranked flaw: a fresh planner proposal (`workflow/plan.py`); a bounded
change by a fresh builder (tool behavior, response content, description, guidance,
or a new command through the capability route); independent validation; and a
baseline/candidate comparison with fixed agent, tasks, evaluator and budgets on at
least two families plus one held-out family. Keep or reject on the pre-declared
rule. A kept change becomes a PR to `main` with tests, changelog and version bump.
Then take the next flaw. Prefer changes that remove a class of friction (a clearer
response, a better default, a missing operation, a misleading description) over
advice for one task.

Done when two cycles have completed end to end on 0.4.0 with recorded verdicts,
kept or rejected.

### M4 — Held-out family bank (complete, 2026-09-10)

Keep a sealed list of families and parameterizations unused in discovery. Spend one
per validation and replace it. Record in `workflow/HELD_OUT.md` which was used when,
so generalization claims stay honest.

Implemented with two locally verified sealed families, immutable payload hashes,
a durable allocation/closure ledger, and fourteen lifecycle tests. Read
[HELD_OUT.md](workflow/HELD_OUT.md) before any future validation allocation.

### M0b — Re-baseline on the released 0.4.1 (complete, 2026-09-10)

Update the plugin in the dedicated Rhino through the Package Manager, restart it,
run `select_release` against `releases/0.4.1`, and run the release pilot once per
family. Then re-rank the flaws: fifteen of the nineteen M2 failures were the
attribute defect 0.4.1 fixes, so the M1/M2 ranking is stale. The next M3 cycles
come from the new ranking, not the old one.

Done when `current-baseline.json` points at 0.4.1 and `flaw-report.json` is rebuilt
from runs on 0.4.1.

### M3b — Continued cycles on the host (complete, 2026-09-10)

Same loop as M3, on the 0.4.1 ranking, with these rules:

- **Fast lane.** Server-only interventions (descriptions, packaged guidance,
  response shaping, Python-side validation) need no Rhino restart. Run those cycles
  on the host now, without waiting for M5. Plugin candidates wait for M5.
- **Execution tools in full-catalog runs.** Until M5 is complete, the gateway must
  refuse and record `run_command`, `execute_rhinoscript_python_code` and
  `execute_rhinocommon_csharp_code` instead of executing them. The attempt is the
  flaw signal; running agent-authored code in the supervisor's Rhino is not.
- **Cross-agent transfer.** A kept description or guidance change must also show no
  regression on the Claude adapter (task success and failed calls) before it ships.
  Comparison orchestration stays Codex-only; the Claude check is a fixed pilot run
  on the frozen candidate.
- **Plugin candidates.** They still go through the existing supervised lifecycle,
  as in M3, when a person is available for the install and restart tickets. When
  nobody is, run server-only cycles.

Done when two more cycles have completed end to end on the 0.4.1 ranking, kept or
rejected, at least one of them server-only, each with the cross-agent check recorded.

### M3c — Behavior cycles on the 0.4.1 findings (next)

Three wording cycles in a row produced nothing measurable while the runs recorded
real behavior defects. Fix the gates first, then work the defects.

**Keep rule v2, for every comparison from now on.**

- Failed calls caused by the gateway (`host_execution_refusal`,
  `host_component_refusal`, scope and budget refusals) are excluded from the
  failed-call gate. They stay in the audit as friction observations.
- With two AB/BA pairs per task, a rejection on failed calls needs a difference of at
  least two non-gateway failures on one task, or a lost success. Anything smaller is
  `inconclusive`: neither kept nor rejected. An inconclusive candidate may be re-run
  with two more frozen pairs, without any tuning, before a verdict.
- A kept change still needs every candidate output to pass, no lost success, the
  Claude check, and a PR to `main`.
- `no change needed` is a legitimate outcome of a cycle. Record it and move on;
  never manufacture a candidate in order to have something to compare.

**Grasshopper allowlist.** Replace the 35-component allowlist with an exclusion
rule: every stock component installed with Rhino 8's Grasshopper is allowed except
script components (C#, Python, VB), file and network I/O, and anything from a
non-stock plugin. Build the list from `gh_get_available_components` on the
dedicated Rhino, review it once, pin its hash, and keep recording refusals
separately from tool failures.

**Targets, in order. The first three and the last are server-only fast lane.**

1. Parameter selector precedence: when `output_name` or `input_name` is given, the
   wrapper must not send the default index. Add regression tests; ship via PR; then
   re-run the Grasshopper discovery suite to see what the fix changes.
2. `gh_build_graph` value targets: determine from the traces whether the confusion
   is the schema shape or the description, and fix the shape if it is the shape.
3. Missing layer on `update_object_attributes` and `create_layer`: when the plugin
   reports a missing layer, the server enriches the error with the existing layer
   full paths (one extra read-only round trip) so the agent can correct in one step.
   Measure on the assembly and joining families.
4. The SURFACE path (plugin, supervised): take the panel traces and the M1
   surface-input findings to a fresh planner. A candidate may need a plugin change
   and therefore a person for the install ticket.
5. Field traces (a product feature): an opt-in `RHINO_MCP_TRACE=<path>` that logs
   tool name, argument shape, duration and error text to a local file, with no
   geometry and no upload, so the user's own modeling sessions can feed the M1
   classifier. Synthetic tasks only find what they were written to find.

Done when targets 1 to 3 each have a verdict under keep rule v2 and the widened
Grasshopper catalog has replaced the allowlist with a pinned review.

**Hygiene, from now on.** Edit the state section above in place instead of
prepending a "latest" block. Store paths in evidence relative to the repository.
Keep each cycle's tracked evidence under about 500 KB; per-call dumps stay in the
ignored run directories. Commit bodies say what was verified.

### M5 — Unattended operation in a Parallels VM (decided 2026-09-10, deferred)

**Deferred by the user on 2026-09-10 until a proper setup exists. Do not start M5a
without an explicit go. The plan below stays as written for when that comes.**

The candidate side (plugin build, candidate Python server, modeling agent, Rhino)
runs in a fresh Parallels guest restored from a clean snapshot for every trial. The
host keeps the controller, evaluators, journals and the trusted judge: the host's
dedicated Rhino on the released baseline, whose listener binds loopback only.
Candidate code never runs on the host. Full boundary and evidence list:
[ISOLATED_ENVIRONMENT.md](workflow/ISOLATED_ENVIRONMENT.md).

**M5a — Feasibility spike (supervised, time-boxed to one day).** Create a fresh
guest with `prlctl` (never the personal `Windows 11.pvm`); prove snapshot restore,
`prlctl exec`, shared folders off, and a network policy that allows Rhino licensing
but nothing on the host except the controller's channel. Inside the guest install
Rhino 8 with a dedicated login, rhinomcp 0.4.1 from the Package Manager, Python and
uv, and the Codex CLI; prove `mcpstart` and `describe_capabilities`; prove Rhino
starts from a command line with `mcpstart` in a startup script, so the lifecycle
needs no desktop clicks. Record the clean snapshot's identity (snapshot id, Rhino
version, plugin SHA and MVID). Pick the guest OS by what passes the spike; Windows
11 ARM is the likely choice on this hypervisor. Check whether one Rhino license lets
host and guest run at the same time; if not, sequence them (the design already
stops the guest before judging) or ask the user for a second seat.
Done when two restores in a row reproduce the identity and a working `mcpstart`.

**M5b — Guest transport and lifecycle.** Add a guest module (for example
`experiments/guest.py`) with restore, start, push-bundle, exec, pull-artifacts and
stop, built on `prlctl`. Bundles carry a reviewed source tree, tasks, tool catalog
and prompts inward; only `.3dm`, `.png`, `.json` and `.jsonl` under the run
directory come back, size-capped, path-checked and hashed on arrival. Replace the
supervised lifecycle tickets in `rhino_trial.py` and `trial.py` with these guest
operations; the host's own Rhino is never restarted by a trial.
Done when the controller installs and exercises a candidate build in the guest end
to end with no desktop interaction, and the restored identity matches.

**M5c — Trusted judge separation.** Models pulled from the guest are hashed, the
guest is stopped, and the host's Rhino measures them with the existing saved-file
evaluators (`evaluate_saved`, trusted-baseline mode). Guest-declared verdicts are
observations only.
Done when the calibration fixtures evaluated through this path reproduce their
known verdicts, and an altered guest verdict file cannot change the host verdict.

**M5d — Denial tests and unattended enablement.** Automate the five evidence
items in ISOLATED_ENVIRONMENT.md with recorded actual denials: guest code trying to
read host user files, alter controller journals, reach the host listener or read
judge inputs; killing guest Rhino, Python and the VM mid-run leaves the host and the
selected baseline intact and the run resumable; a restored snapshot keeps its
identity; one complete capability comparison passes through the isolated path.
Add wall-clock and provider-cost caps to campaigns. Only then enable unattended
acceptance for this environment. A PR to `main` remains the human gate for
shipping; nothing publishes automatically.
Done when `workflow/ISOLATION_EVIDENCE.md` records all five items with hashes and a
campaign of at least three comparisons has run overnight without a person.

### M6 — Grasshopper harness (complete, 2026-09-10; M5 deferred)

Same cycle, different surface, on the host, supervised like M3.

- Tasks: text descriptions of small definitions with checkable outputs, such as a
  grid of N cylinders whose height follows a point attractor, a lofted surface from
  three sliders, or a series of sections through a given solid. Fresh agents get the
  `gh_*` tools only; every attempt starts from `gh_create_document`.
- Evaluator: read the definition with `gh_get_graph` and `gh_get_document_info`,
  run it with `gh_run_solution`, check outputs with `gh_get_parameter_value`
  (counts, values, bounds) and use `gh_capture_preview` for supplementary images.
  Deterministic checks: the solution runs without errors, required components and
  connections exist, no orphan components, outputs within tolerance. A bake-to-
  document command may be the first capability proposal, so the existing saved-file
  evaluators can judge the geometry.
- Flaw taxonomy additions: component search churn, wrong parameter names or
  indices, wiring errors, repeated expire/run loops, layout thrash.
- Reuse the runner, gateway pattern, audit and comparison code; add a Grasshopper
  evaluator adapter and task type, and nothing else new in orchestration.

First steps, in order:

1. Ownership and cleanup for Grasshopper documents in the gateway: an equivalent
   of `assert_document` for the active Grasshopper document, every attempt starting
   from `gh_create_document` and ending with `gh_clear_canvas`, while the Rhino
   document stays owned and empty as today. Today's full-catalog gateway refuses
   `gh_*` calls; the Grasshopper gateway exposes only them.
2. A `gh_definition` task type and schema: text instruction, required outputs
   (parameter names, expected counts, values or bounds with tolerances), budgets.
   The saved artifact is the graph from `gh_get_graph` plus the output values after
   `gh_run_solution`, hashed the way `.3dm` files are.
3. An evaluator adapter registered like `workflow_scene`: the solution runs without
   errors, required components and connections exist, no orphan components, outputs
   within tolerance. Calibrate with correct and flawed fixtures before any discovery.
4. Fresh discovery runs with the `gh_*` tools only, then the flaw ranking with the
   Grasshopper classes added. A bake-to-document command is the expected first
   capability proposal, so the saved-file evaluators can judge the geometry.

Done when at least three definition families are calibrated, have fresh baseline
runs on 0.4.1, and one Grasshopper improvement cycle has completed end to end.

## Pointers

- `workflow/README.md`: cycle, tolerance policy, implemented comparison machinery.
- `harness/README.md`: where each rule lives; role prompts in `harness/roles/`.
- `workflow/current-baseline.json` and `workflow/historical.json`: pins and registry.
- `workflow/ISOLATED_ENVIRONMENT.md`: what M5 needs from the user.
- `HANDOFF_HISTORY.md`: every previous handoff, verbatim, for provenance.
- `../docs/AUTONOMOUS_IMPROVEMENT_PLAN.md`: long-form roadmap and phase history.
- `roadmap.html`: visual snapshot; add real screenshots at modeling milestones.
