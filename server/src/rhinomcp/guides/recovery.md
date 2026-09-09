# Recover without repeating uncertain edits

After an error, lost connection or interrupted session, inspect the active document,
known object IDs and current geometry before retrying a mutation. An interrupted
response does not prove that Rhino did not execute the operation. Blind repetition
can create duplicates or transform an object twice.

Distinguish invalid inputs, unsupported operations, transport failures, incorrect
modeling choices and suspected tool defects. Read tool errors and compare the saved
or live geometry with the request. Keep failed artifacts or diagnostic screenshots
when they are useful; do not label a failed result as accepted.

Limit cleanup to objects known to belong to this task. Do not delete unrelated,
hidden or locked user work. If ownership is uncertain, stop the destructive cleanup
and clarify the affected objects. Preserve the user's document rather than resetting
it to make an experiment succeed.

If retrying, use the observed state and a bounded plan. Verify after each uncertain
step. Do not change the required geometry, relax tolerances, or omit a failed check
just to obtain a passing result. Plugin rebuilding, automatic installation and
experimental baseline replacement belong to the contributor harness, not a normal
modeling session.
