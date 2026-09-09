# Declared new-command builder

The new `capability.py` / `capability_mcp.py` route is separate from the existing
edit-only defect builder. It consumes a validated `new_capability` workflow proposal
and an explicit supervisor review, exports a pinned production revision, starts a
fresh builder, and stops at a patch for source review. It never builds, installs or
promotes that patch.

The scope declares the command-to-handler mapping, exact Python/C#/schema additions,
existing protocol/envelope edits, a declared command-test file and readable source paths. Missing declarations,
traversal, hidden harness paths, overwrites, stale replacement hashes, modified
manifests, symlinks, extra files, deletions and protected mode/content changes fail.
Only the exact new files and necessary parent directories may be created. Existing
repair permissions are unchanged.

The final gate requires native tool registration, a matching transport command,
matching C# command registration, a closed parameter schema, protocol enum membership
and protocol-envelope test membership. Those static checks are an integrity and
completeness screen. They cannot prove correct C# semantics, useful geometry or
preservation of behavior. The supervisor must review the full patch and then run
candidate developer checks and independent live comparisons. File restrictions are
not an OS security boundary against adversarial code.

Thirteen focused tests exercise complete candidates, missing tiers/coverage, wrong
transport/handler/schema, protected edits, additions, symlinks, mode changes and
manifest/compare-before-write enforcement. A fresh planar-region proposal has produced a candidate and review revision.
Its Python/schema checks pass, and a 79-case live trial is prepared; C# build and
live validation are still pending. A missing capability must be supported
by workflow evidence before dispatch; infrastructure tests do not establish a new
useful RhinoMCP tool.

```sh
PYTHONPATH=. server/.venv/bin/python -m experiments.capability /absolute/scope.json /absolute/proposal.json --review-file /absolute/review.txt
```

A complete end-to-end capability trial and integration with independent build,
comparison and selection remain required before marking the capability milestone
finished.

The existing trial intake now recognizes pinned capability manifests and verifies
the whole checkout and complete new-file review diff before copying source into an
immutable trial. Edit-only defect checks remain unchanged. A fresh revision route
retains prior checkpoints/patches and forbids revision after trial registration.
