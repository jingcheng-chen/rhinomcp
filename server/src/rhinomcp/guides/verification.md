# Verify geometry against the task

Use analyze_objects with one explicit target selector. Check validity, intended
surface/solid status, dimensions, world bounds and available topology measurements.
A closed solid alone does not establish correct geometry. Volume alone cannot prove
hole placement, and area alone cannot prove a surface's boundary or world position.

For solids, check closure and volume together with bounds and representative interior
or exterior points when available. For surfaces, check face/loop counts, boundaries,
area and sampled shape. Use measurements suitable for the particular geometry;
finite samples are evidence, not a guarantee between every sampled point.

Inspect the whole deliverable for extra construction geometry, including hidden or
locked objects. Do not confuse a filtered object list with the entire document.
Compare the actual count with the requested final count while preserving unrelated
user objects. Check layers and intended names separately from shape.

Use screenshots to inspect appearance and clearly label the view. Auto-fitted views
can hide a wrong translation or scale. Pictures do not replace numeric world-pose
checks, topology or a saved-file audit. Preserve the user's camera and display setup
when changing views for inspection.

For deliverables, verify the saved model when practical rather than accepting only
the live viewport. Report passing checks, failures and unmeasured requirements
separately. Do not claim a tool improvement from one successful model or claim broad
reliability from a small collection of examples.
