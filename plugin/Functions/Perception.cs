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
    /// The id lists are capped so a single operation over a large model can't
    /// flood the client's context with thousands of GUIDs. The counts are
    /// always exact; the id arrays are only included when at or under the cap,
    /// and `truncated` flags when one was dropped. This mirrors how
    /// GetDocumentSummary summarizes rather than enumerates.
    /// </summary>
    public const int DeltaIdListCap = 50;

    /// <summary>
    /// Build a change-delta from before/after id snapshots taken around a
    /// command. created_count and deleted_count are exact set differences,
    /// immune to the read-after-delete pitfall (they compare ids and never
    /// re-read an object). A modified count is intentionally absent: an in-place
    /// transform reuses the same id, so it isn't derivable from ids alone, and a
    /// half-defined field would be worse than none. count_before/count_after
    /// carry the net effect even when nothing was created or deleted. The actual
    /// created_ids/deleted_ids arrays are included only when small enough to be
    /// useful without flooding the response (see DeltaIdListCap).
    /// </summary>
    public JObject BuildDelta(HashSet<Guid> before, HashSet<Guid> after)
    {
        before ??= new HashSet<Guid>();
        after ??= new HashSet<Guid>();

        var created = new List<string>();
        foreach (var id in after)
        {
            if (!before.Contains(id)) created.Add(id.ToString());
        }

        var deleted = new List<string>();
        foreach (var id in before)
        {
            if (!after.Contains(id)) deleted.Add(id.ToString());
        }

        var delta = new JObject
        {
            ["created_count"] = created.Count,
            ["deleted_count"] = deleted.Count,
            ["count_before"] = before.Count,
            ["count_after"] = after.Count
        };

        bool truncated = false;
        if (created.Count <= DeltaIdListCap)
            delta["created_ids"] = new JArray(created);
        else
            truncated = true;
        if (deleted.Count <= DeltaIdListCap)
            delta["deleted_ids"] = new JArray(deleted);
        else
            truncated = true;
        delta["truncated"] = truncated;

        return delta;
    }
}
