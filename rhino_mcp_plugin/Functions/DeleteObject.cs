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
        bool all = parameters.ContainsKey("all");
        
        if (all)
        {
            doc.Objects.Clear();
            doc.Views.Redraw();
            return new JObject()
            {
                ["deleted"] = true,
            };
        }
        
        
        var obj = getObjectByIdOrName(parameters);

        bool success = doc.Objects.Delete(obj.Id, true);

        if (!success)
            throw new InvalidOperationException($"Failed to delete object with ID {obj.Id}");

        // Update views
        doc.Views.Redraw();

        return new JObject
        {
            ["id"] = obj.Id,
            ["name"] = obj.Name,
            ["deleted"] = true
        };
    }
}