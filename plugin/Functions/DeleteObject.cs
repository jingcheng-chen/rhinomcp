using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("delete_object")]
    public JObject DeleteObject(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        bool all = parameters["all"]?.ToObject<bool>() == true;
        bool hasId = parameters["id"] != null;
        bool hasName = parameters["name"] != null;

        // Defense-in-depth: schema + Python wrapper already reject mixed selectors,
        // but the TCP path is not currently schema-validated, so guard here too —
        // an `{id, all: true}` payload would otherwise wipe the document.
        if (all && (hasId || hasName))
            throw new InvalidOperationException("delete_object: 'all' cannot be combined with 'id' or 'name'.");

        if (all)
        {
            // Delete object by object, not ObjectTable.Clear(): Clear() bypasses
            // the undo record the dispatcher opened, so one wrong call wiped the
            // model with no way back (issue #89). Deleted this way, one Ctrl+Z
            // (or the undo tool) restores everything.
            var ids = doc.Objects.Select(o => o.Id).ToList();
            int deleted = ids.Count == 0 ? 0 : doc.Objects.Delete(ids, true);
            doc.Views.Redraw();
            var result = new JObject()
            {
                ["deleted"] = true,
                ["count"] = deleted,
                ["scope"] = "all",
            };
            // Locked objects, and objects on locked layers, are not deleted.
            if (deleted < ids.Count)
                result["skipped_count"] = ids.Count - deleted;
            return result;
        }

        if (!hasId && !hasName)
            throw new InvalidOperationException("delete_object requires id, name, or all=true.");

        var obj = getObjectByIdOrName(parameters);

        bool success = doc.Objects.Delete(obj.Id, true);

        if (!success)
            throw new InvalidOperationException($"Failed to delete object with ID {obj.Id}");

        // Update views
        doc.Views.Redraw();

        return new JObject
        {
            // Coalesce to match Serializer.RhinoObject: an object with no name
            // reports "(unnamed)", never null. delete_result.json types name as a
            // string, so emitting null here made deleting an unnamed object fail
            // response validation.
            ["id"] = obj.Id,
            ["name"] = obj.Name ?? "(unnamed)",
            ["deleted"] = true
        };
    }
}