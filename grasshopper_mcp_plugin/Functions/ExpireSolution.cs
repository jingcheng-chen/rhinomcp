using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Expire and recompute specific components or the entire solution.
    /// </summary>
    public JObject ExpireSolution(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var componentIds = parameters["component_ids"]?.ToObject<string[]>();
        var expireDownstream = parameters["expire_downstream"]?.ToObject<bool>() ?? true;
        var recompute = parameters["recompute"]?.ToObject<bool>() ?? true;

        int expiredCount = 0;

        if (componentIds != null && componentIds.Length > 0)
        {
            // Expire specific components
            foreach (var idStr in componentIds)
            {
                if (Guid.TryParse(idStr, out var guid))
                {
                    var obj = doc.FindObject(guid, true);
                    if (obj != null)
                    {
                        obj.ExpireSolution(expireDownstream);
                        expiredCount++;
                    }
                }
            }
        }
        else
        {
            // Expire all components
            foreach (var obj in doc.Objects)
            {
                obj.ExpireSolution(false);
                expiredCount++;
            }
        }

        // Trigger recompute if requested
        if (recompute)
        {
            doc.NewSolution(false);
        }

        return new JObject
        {
            ["expired_count"] = expiredCount,
            ["recomputed"] = recompute,
            ["message"] = $"Expired {expiredCount} component(s)" + (recompute ? " and triggered recompute" : "")
        };
    }
}
