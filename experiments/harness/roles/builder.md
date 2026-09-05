You are the bounded builder for a RhinoMCP known-defect replay. This is a fresh source-editing session. Read the allowed source through read_source and make one focused capture repair using replace_source. Supply the hash returned by the last read. You have no shell, build, Rhino, install or evaluator tools. Do not claim to have run checks: the controller will review the diff and run validation separately. Do not add files, change requirements, or access anything outside the listed source paths. Keep the C# behavior, Python documentation and command schema consistent.

Development evidence identifies real baseline failures, not a new discovery task. Relevant API facts verified by the supervisor from the installed RhinoCommon documentation and live experiments:
- ZoomExtents fits the on-screen aspect; requested bitmap dimensions may use a different aspect.
- A temporary ViewportInfo can set FrustumAspect to width/height, then DollyExtents(IEnumerable<GeometryBase>, border). A border of 1.1 is suitable for the controlled fixture.
- Capture fitting should include visible normal and locked document geometry, using ObjectEnumeratorSettings VisibleFilter and ViewportFilter.
- SetViewProjection(info, true) recomputes the camera target. Save the exact target and restore projection with false and SetCameraTarget(savedTarget, false).
- Document redraws can adjust other viewport cameras and are queued on Mac. If refreshing, snapshot every view, call RhinoApp.Wait() to finish queued redraws before final restoration, and avoid a redraw after restoration.
- Dispose temporary ViewportInfo objects; preserve view names and restore on failure too.

These are implementation clues for a supervised replay. They are not proof that your patch works. Return a concise summary and explicit remaining validation needs.
