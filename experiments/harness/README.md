# Harness definition

This directory contains the active agents' role instructions. `../runner.py`
loads these files when assembling each session prompt; they are executable
configuration, not a second copy of instructions kept elsewhere.

| Concern | Source of truth |
| --- | --- |
| Modeler behavior | `roles/modeler.md` |
| Planner behavior | `roles/planner.md` |
| Modeling tasks and expected measurements | `../tasks/box.json`, `../tasks/posed_prism.json`, `../tasks/through_hole.json` |
| Supported task types and input contract | `../tasks/schema.json` |
| Role order, context assembly, session launch, timeouts, output schemas | `../runner.py` |
| Permitted modeling operations and call budget | `../modeler_mcp.py` |
| Document identity guard and controller-only execution | `../bridge.py` |
| Trusted saved-file measurements and acceptance | `../evaluate.cs`, `../evaluator.py` |
| Live capture framing and viewport-preservation regression | `../validate_capture.py` |
| Build, installation, Rhino startup, execution and recovery | `../README.md` |
| Development handoff and next milestone | `../CONTINUE.md` |
| Actual prompts, tool calls, evidence and decisions | `../runs/<run>/` (local, ignored by Git) |

Changing Markdown does not grant permissions. The controller and gateway enforce
tool access and output contracts. The deterministic evaluator is ordinary code,
not an AI role. Builder and QA-reviewer sessions are still planned; no dormant
role files should be mistaken for implemented stages.

For every invocation the runner saves the assembled prompt and output schema,
so past runs retain the instructions they actually used even after role edits.
Runs also snapshot evaluator sources and record their hashes. Evaluator corrections
belong to the supervising development workflow, never to a plugin builder seeking
to pass its own candidate. Preserve old verdicts and validate corrections with
independent fixtures before starting another experiment.
Maintain one source for each rule. Extract additional schemas or adapter modules
when their complexity warrants it; a top-level `harness/` rename is unnecessary.
