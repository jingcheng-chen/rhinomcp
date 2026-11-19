# Bundles of geometry operations

RhinoMCP does not add packages of geometry tools ("advanced NURBS
surfaces", "all of Rhino's surface commands") ahead of evidence that
agents need them.

## Why this is out of scope

The agent can already reach every Rhino operation:

- Dedicated tools cover the operations agents use most: `loft`, `sweep1`,
  `pipe`, `extrude_curve`, `offset_curve`, `split_curve`,
  `project_curve`, `section_profile`, the three booleans, and
  `create_planar_region`.
- Everything else is reachable through `execute_rhinoscript_python_code`
  (rhinoscriptsyntax) and `execute_rhinocommon_csharp_code` (all of
  RhinoCommon), and the `rhinoscript_docs` tools help the agent find the
  right function.

Each dedicated tool costs three tiers of upkeep (Python wrapper, C#
handler, JSON contract) and adds to the tool list every model reads on
every turn. A long list of rarely used tools makes tool choice worse
rather than better.

The project's direction is to improve modeling workflows by finding where
agents actually fail in recorded runs (see `experiments/CONTINUE.md`). A
new geometry tool earns its place when those runs show agents repeatedly
failing at an operation through the script tools, and the request names
that specific operation, the failing call, and what went wrong.

## What to file instead

An issue about one operation, with the prompt, the tool calls the agent
made, and the wrong result. That is a bug or enhancement this project
will triage normally.

## Prior requests

- #21: "Feature Request: Advanced NURBS Surface Operations Package"
