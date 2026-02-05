using System;
using Grasshopper;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Delete a component from the Grasshopper canvas.
    /// Supports instance_id, nickname, or component_id.
    /// </summary>
    public JObject DeleteComponent(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Find component - supports instance_id, nickname, or component_id
        var obj = ComponentHelper.FindComponent(doc, parameters);

        var name = obj.Name;
        var deletedNickname = obj.NickName;
        var deletedId = obj.InstanceGuid.ToString();

        // Remove from document
        doc.RemoveObject(obj, false);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["deleted_id"] = deletedId,
            ["nickname"] = deletedNickname,
            ["name"] = name,
            ["message"] = $"Deleted component '{deletedNickname}' ({name})"
        };
    }
}
