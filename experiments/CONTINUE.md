# Continue autonomous RhinoMCP improvement

Entry point for a fresh development session (Codex CLI or Claude Code) with no
chat context. Last updated 2026-09-09, after the 0.4.0 release. Verify repository
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
6. Ask the user only for: the dedicated isolation environment (M5); any change to a
   released tool's wire contract that would break older clients or plugins; and
   anything touching user documents or the installed Rhino outside the dedicated
   test session. Decide and record everything else yourself.
7. Before every commit: from `server/`, `.venv/bin/python -m pytest` (285 at last
   count) and `.venv/bin/ruff check src/rhinomcp`; from the repository root,
   `server/.venv/bin/python -m pytest experiments/tests` (355) and
   `server/.venv/bin/python -m pytest contracts/test_schemas.py` (13); for plugin
   changes, `dotnet build plugin/rhinomcp.sln --configuration Release`.

Do not: build object-specific runners; resume chair or cushion work; add
construction recipes to guidance without a cross-task flaw that motivates them;
promote a candidate automatically; leave a controller or agent running; paste
credentials anywhere; reinstall the plugin into a Rhino that holds user work.

## Current state — 2026-09-09

- Released: rhinomcp 0.4.0 on PyPI and Yak from `releases/0.4.0`; `main` is at the
  merge of PR #52 (`a4bb8bb`). 0.4.0 includes MCP SDK 2.x, `create_planar_region`,
  packaged guidance v2, the plugin repairs, and the server/plugin version-skew guard.
  `CHANGELOG.md` has the details. The `harness` branch is merged; keep developing on it.
- Every Rhino connection now reads `describe_capabilities` once before its first
  command. Traces show that call; it is not an agent decision.
- `workflow/current-baseline.json` still names the pre-release planar build and a
  local naked-edge overlay. Both are superseded by the released 0.4.0 plugin (M0).
- Last known local runtime, to re-verify: the naked-edge build
  (MVID `addb4d4c-9ce9-4021-b777-53b34874e663`), not the released binary. The
  release session did not install 0.4.0 into Rhino.
- Discovery so far: five families audited historically (primitives, posed solids,
  subtractive solids, surface construction, layer organization, plus photo
  reconstruction); the native pilot covers primitives, subtractive solids, posed
  solids, trimmed patches and curved panels through a 14-tool subset. Held-out cases
  in those families are spent; new parameterizations of them are discovery cases.
- Agents available: the Codex adapter (default) and the Claude adapter (native
  modeling validated; binary comparison orchestration remains Codex-only).
- Pending user decision: the dedicated isolation environment (VM or machine) for
  unattended operation. Nothing else blocks M0 to M4.
- Tests at last verification: 285 server, 355 experiments, 13 contracts.

## Milestones from here, in order

Each milestone ends with tests green, a portable report under `workflow/`, the
state section above updated, and a commit.

### M0 — Re-baseline on the released 0.4.0

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

### M1 — Flaw detection from traces

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

### M2 — Realistic workflow families

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

### M3 — One improvement cycle per flaw

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

### M4 — Held-out family bank

Keep a sealed list of families and parameterizations unused in discovery. Spend one
per validation and replace it. Record in `workflow/HELD_OUT.md` which was used when,
so generalization claims stay honest.

### M5 — Unattended operation and hard isolation (blocked on the user)

Needs the dedicated environment decision. Until then run supervised only; do not
enable automatic promotion or installation. See `workflow/ISOLATED_ENVIRONMENT.md`.

### M6 — Grasshopper harness (later)

Same cycle, different surface; refine once M1 to M3 have run at least once.

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

## Pointers

- `workflow/README.md`: cycle, tolerance policy, implemented comparison machinery.
- `harness/README.md`: where each rule lives; role prompts in `harness/roles/`.
- `workflow/current-baseline.json` and `workflow/historical.json`: pins and registry.
- `workflow/ISOLATED_ENVIRONMENT.md`: what M5 needs from the user.
- `HANDOFF_HISTORY.md`: every previous handoff, verbatim, for provenance.
- `../docs/AUTONOMOUS_IMPROVEMENT_PLAN.md`: long-form roadmap and phase history.
- `roadmap.html`: visual snapshot; add real screenshots at modeling milestones.
