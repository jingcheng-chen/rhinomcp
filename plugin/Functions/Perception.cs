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

    /// <summary>
    /// The issues list is capped so a pathological write that produces many
    /// invalid objects can't flood the response. invalid_count is always exact;
    /// the issues array holds at most this many entries, and the health block's
    /// `truncated` flag is set when some were dropped. Same summarize-don't-
    /// enumerate shape as the change-delta.
    /// </summary>
    public const int HealthIssueCap = 50;

    /// <summary>
    /// Build a geometry-health report over the objects a command just created
    /// (the set difference after - before, the same newly-created ids the
    /// change-delta reports). Each created object is checked with
    /// GeometryBase.IsValidWithLog, which returns the verdict and a human-readable
    /// reason in one pass. checked_count and invalid_count are always exact; only
    /// the invalid objects are listed, with their reason, so a clean write returns
    /// an empty issues array rather than a wall of "ok".
    ///
    /// Scope mirrors the change-delta: created geometry only. An in-place modify
    /// reuses its id, so it can't be told apart by a set diff, and validity rarely
    /// changes under a rigid transform; rather than special-case it per handler at
    /// the cost of a half-covered field, this reports the new geometry that every
    /// mutator funnels through here produces. The big win is the arbitrary-code and
    /// boolean/loft paths, where an invalid result can otherwise land silently.
    /// </summary>
    public JObject BuildHealth(RhinoDoc doc, HashSet<Guid> before, HashSet<Guid> after)
    {
        before ??= new HashSet<Guid>();
        after ??= new HashSet<Guid>();

        int checkedCount = 0;
        int invalidCount = 0;
        var issues = new JArray();

        foreach (var id in after)
        {
            if (before.Contains(id)) continue;            // only newly created objects
            var geo = doc?.Objects.FindId(id)?.Geometry;
            if (geo == null) continue;                    // not resolvable / nothing to judge
            checkedCount++;
            if (!geo.IsValidWithLog(out string log))
            {
                invalidCount++;
                if (issues.Count < HealthIssueCap)
                {
                    issues.Add(new JObject
                    {
                        ["id"] = id.ToString(),
                        ["reason"] = (log ?? "").Trim()
                    });
                }
            }
        }

        return new JObject
        {
            ["checked_count"] = checkedCount,
            ["invalid_count"] = invalidCount,
            ["issues"] = issues,
            ["truncated"] = invalidCount > HealthIssueCap
        };
    }
}
