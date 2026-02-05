using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Delete a component from the Grasshopper canvas.
    /// </summary>
    public JObject DeleteComponent(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Get component identifier
        var instanceId = parameters["instance_id"]?.ToString();
        var nickname = parameters["nickname"]?.ToString();

        if (string.IsNullOrEmpty(instanceId) && string.IsNullOrEmpty(nickname))
        {
            throw new ArgumentException("Either instance_id or nickname is required");
        }

        IGH_DocumentObject? obj = null;

        // Find by instance ID
        if (!string.IsNullOrEmpty(instanceId) && Guid.TryParse(instanceId, out var guid))
        {
            obj = doc.FindObject(guid, true);
        }

        // Find by nickname
        if (obj == null && !string.IsNullOrEmpty(nickname))
        {
            obj = doc.Objects.FirstOrDefault(o => o.NickName == nickname);
        }

        if (obj == null)
        {
            throw new InvalidOperationException($"Component with ID '{instanceId}' or nickname '{nickname}' not found");
        }

        var name = obj.Name;
        var deletedId = obj.InstanceGuid.ToString();

        // Remove from document
        doc.RemoveObject(obj, false);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["deleted_id"] = deletedId,
            ["name"] = name,
            ["message"] = $"Deleted component '{name}'"
        };
    }
}
