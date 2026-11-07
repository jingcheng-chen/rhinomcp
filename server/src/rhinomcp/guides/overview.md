# Rhino modeling workflow

Use this guide with the tool schemas exposed by your installed server. These are
reusable modeling practices, not a recipe for a particular object.

1. Call get_context before the first edit of a task and again after large changes.
   It reports units, tolerances, current layer, object counts, selection and camera
   in one bounded call; nothing is sent automatically. Use get_document_summary only
   when the layer hierarchy or per-layer counts matter. Identify existing work, units
   and relevant layers. Do not clear a user's document or assume that an empty
   document from an earlier session is still active. Use set_camera or zoom_to to
   look where the work is.
2. Translate the request into measurable requirements: dimensions, world position,
   intended surfaces versus solids, openings, object count and organization. Keep
   unspecified details separate from known requirements.
3. Choose an available typed operation: create_object for primitives and curves,
   create_planar_region for a planar face with optional holes, extrude_curve for a
   profile extrusion, loft or sweep1 for their respective constructions, and boolean
   tools for solid combinations. Read the actual schemas before supplying arguments.
   For scripts, consult get_rhinoscript_docs instead of guessing API signatures.
4. Plan transforms explicitly. Creation anchors and rotation pivots vary by tool.
   Retrieve the transforms topic before composing rotations, scales or world poses.
5. Keep returned object IDs and distinguish construction geometry from final objects.
   Use meaningful names and hierarchical layers; retrieve organization for details.
6. Verify the result against the requirements using analyze_objects, object queries
   and appropriate shape checks. A successful call or completion message is not proof
   that the model matches the request. Read the capture_viewport metadata before
   trusting a picture. Retrieve verification for the checks to use.
7. Remove only construction objects created for this task after the result is
   verified. On failure or interruption, inspect current state before retrying;
   retrieve recovery. Report remaining uncertainty rather than silently weakening
   the requirements.

Available guide topics: overview, transforms, planar_regions, organization,
verification, recovery. Read only the topics relevant to the current task.
