# Attribute update regression checks

Use a disposable Rhino document. Start `mcpstart`, then call the MCP tools below.
Run each check on a fresh box so visibility or locking does not affect later cases.

1. Create a box and record its ID and bounds. Create another layer.
2. Call `update_object_attributes` with the ID and only `layer` set. Expect success
   and the same ID/geometry on that layer. Released 0.4.0 on Rhino 8 for macOS
   fails here with the unavailable `JToken.ToString(Formatting)` method.
3. On a fresh object, seed `old=value` using Rhino's user text interface. Update
   `user_strings` with `text: 'quoted "value"'`, `integer: 42`, `decimal: 1.25`,
   `true: true`, `false: false`, and `remove: null`. Read back user text: the old
   entry remains, strings stay native, numbers/booleans use compact JSON spelling,
   and `remove` is absent. Updating detached attributes prevents silent user-text
   loss when committing through `ModifyAttributes`.
4. Verify `delete_user_strings: ["old"]` and `clear_user_strings: true` separately.
5. On separate objects, verify renaming with RGB color `[13,27,91]`, hiding,
   locking, and `material_index: -1` (inherit from layer).
6. Reject array/object user-string values, simultaneous hidden+locked state,
   nonexistent layers, nonexistent material indices, and a request with no updates.
   Confirm the object's geometry, ID and prior attributes are unchanged on failure.
7. Save and reopen the file. Check all successful changes persist with the original
   geometry and IDs.

## Recorded validation — 2026-09-10

Fourteen independent direct checks passed on the 0.4.1 build, including saved-file
identity/geometry checks and cleanup preservation. Binary SHA-256:
`e11ac653eaa0a503e28ed20a09ead26cdc8974448fbcdae2dab716379a0f3be3`;
MVID `4cf421f0-ac86-44c2-a275-eefba631c337`.

The same two-line handler patch was also compared with released 0.4.0 in twelve
fresh full-catalog agent sessions: two AB/BA pairs for each of assembly, recovery
and held-out planar offset workflows. All twelve saved outputs passed independent
baseline evaluation; the candidate removed the scripting recovery cost rather
than changing final correctness in these full-catalog sessions.

| Family | Median calls, baseline → candidate | Failed calls, baseline → candidate |
| --- | --- | --- |
| Assembly | 21 → 14 | 10 → 0 |
| Recovery | 15 → 10 | 3 → 0 |
| Held-out planar offset | 24 → 18 | 2 → 0 |

Pins: gpt-5.6-terra, medium effort, 70 tool definitions, 50 calls and 240 seconds
per session. Two repeats are descriptive evidence, not statistical proof; backend
model snapshots were unavailable. All files were evaluated after the candidate
stopped and the trusted released plugin was restored. These are supervised local
runs, not an adversarial sandbox.

Local evidence IDs in the development harness: comparison
`workflow-binary-20260910-085542-7d89feb3`; release-build direct checks
`attribute-probe-20260910-093130`. No source or binary promotion was automatic.
