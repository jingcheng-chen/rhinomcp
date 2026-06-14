using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Snapshot the set of object ids currently in the document. Ids and count
    /// only, no geometry, so it is cheap enough to call on the UI thread on
    /// either side of a mutating command. This walks the same object table
    /// GetDocumentSummary does, without the per-object bounding-box touch.
    ///
    /// A pull-based snapshot is deliberate: the plugin subscribes to no RhinoDoc
    /// events, so there is no change stream to tap and nothing async to reason
    /// about. Diffing two snapshots is exact and self-contained.
    /// </summary>
    public HashSet<Guid> SnapshotObjectIds(RhinoDoc doc)
    {
        var ids = new HashSet<Guid>();
        if (doc == null) return ids;
        foreach (var obj in doc.Objects)
        {
            if (obj != null) ids.Add(obj.Id);
        }
        return ids;
    }

    /// <summary>
    /// Build a change-delta from before/after id snapshots taken around a
    /// command. created_ids and deleted_ids are exact set differences, so they
    /// are immune to the read-after-delete pitfall (they compare ids and never
    /// re-read an object). A modified count is intentionally absent: an in-place
    /// transform reuses the same id, so a modification is not derivable from ids
    /// alone, and a half-defined field would be worse than none. count_before
    /// and count_after still carry the net effect even when nothing was created
    /// or deleted (e.g. a pure transform leaves both equal).
    /// </summary>
    public JObject BuildDelta(HashSet<Guid> before, HashSet<Guid> after)
    {
        before ??= new HashSet<Guid>();
        after ??= new HashSet<Guid>();

        var createdIds = new JArray();
        foreach (var id in after)
        {
            if (!before.Contains(id)) createdIds.Add(id.ToString());
        }

        var deletedIds = new JArray();
        foreach (var id in before)
        {
            if (!after.Contains(id)) deletedIds.Add(id.ToString());
        }

        return new JObject
        {
            ["created_ids"] = createdIds,
            ["deleted_ids"] = deletedIds,
            ["count_before"] = before.Count,
            ["count_after"] = after.Count
        };
    }
}
