# Distributable modeling knowledge — accepted product direction

User clarification, 2026-09-09: reusable knowledge learned from the harness must ship
with RhinoMCP for all users, not remain in local memories or chair-specific scripts.

## Implemented

Six canonical Markdown topics live in `server/src/rhinomcp/guides`. The wheel and
source distribution explicitly include them. `get_modeling_guidance(topic)` returns
versioned content without a Rhino connection; an MCP resource exposes the same text,
and the strategy prompt reads the shared overview. Server initialization instructions
advertise discovery. Essential pivot semantics are now also in modify_object's
public description. The stale strategy prompt's incorrect layer assignment advice
is replaced with guidance using update_object_attributes.

This is server-local documentation, so it does not add a TCP command, plugin handler
or geometry behavior. No plugin build/restart was required. Full MCP catalog: 70
(including guide); native benchmark interface: 14. Guide Markdown is now included
in experiment source pins. Old comparisons retain their archived source versions.

Optional client skills may be generated from these canonical topics later; normal
MCP users do not need a separate skill installation. Infrastructure for building,
installing and scoring experimental plugins remains a contributor concern.

## Clean distribution check

Wheel and sdist contain all six topics byte-for-byte. A fresh environment outside
the repo installed the wheel and exercised real MCP initialization, tool discovery,
all guide calls, resource reads, the strategy prompt, and invalid-topic rejection.
Rhino was deliberately unavailable. The check rejects editable source imports and
is reusable as `server/verify_guidance_install.py` with a clean installed Python.

This exposed an existing open-ended dependency installing incompatible MCP 2.x.
The package and lock now constrain the SDK to >=1.16.0,<2, matching the existing
FastMCP-based implementation. The repeated clean installation succeeds.

629 development tests pass; source lint passes. See guidance-distribution.json for
artifact hashes, and runs/guidance-distribution-20260909 for wheel/sdist and logs.
Artifacts still use the current package version 0.3.2 and are LOCAL UNRELEASED BUILDS.
No upload/publication or Git push occurred. A release must assign the intended new
version and include matching server/plugin distribution notes before users upgrade.

## Initial guided modeling observation

Three fresh Claude sonnet/medium sessions used unchanged box, through-hole and
trimmed-reserved task files. All three saved models pass, including the patch whose
world pose failed in the earlier pilot. The patch session read transforms and
planar_regions before constructing its final model. Total: 20 attempts, zero failed
calls, 98.46 modeling seconds; all document fingerprints/source pins preserved.
Read guidance-live-results.json and the roadmap screenshots. Run:
`runs/workflow-baseline-20260909-125308-0fc34223`.

This is a usability observation, not repeated randomized/counterbalanced evidence.
The guide, initialization instructions, tool catalog and pivot description changed
together. Do not attribute the result to one wording change or claim general speed
improvement. Next: compare this declared guidance bundle with the previous interface
on frozen repeated/withheld cases before claiming a measured general workflow gain.

## Roadmap acceptance rule

For each validated lesson, decide whether it belongs in tool behavior, its public
description, canonical modeling guidance, or contributor-only infrastructure.
User-facing knowledge must be versioned, discoverable and verified from release
artifacts with no local experiment dependencies. Proposed but untested advice must
not be labeled proven. Client-specific skill copies must derive from the canonical
source. Hard isolation, provider-role coverage and unattended operation remain open.
