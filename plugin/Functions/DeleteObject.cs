using System;
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
            int count = CountActiveObjects(doc);
            doc.Objects.Clear();
            doc.Views.Redraw();
            return new JObject()
            {
                ["deleted"] = true,
                ["count"] = count,
                ["scope"] = "all",
            };
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