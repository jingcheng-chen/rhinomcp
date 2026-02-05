using System;
using System.Drawing;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Add a component to the Grasshopper canvas.
    /// </summary>
    public JObject AddComponent(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Get component identifier (name or GUID)
        var componentName = parameters["component_name"]?.ToString();
        var componentGuid = parameters["component_guid"]?.ToString();

        if (string.IsNullOrEmpty(componentName) && string.IsNullOrEmpty(componentGuid))
        {
            throw new ArgumentException("Either component_name or component_guid is required");
        }

        // Get position
        var positionArray = parameters["position"]?.ToObject<double[]>() ?? new double[] { 0, 0 };
        var position = new PointF((float)positionArray[0], (float)positionArray[1]);

        // Get optional nickname
        var nickname = parameters["nickname"]?.ToString();

        // Find the component proxy
        IGH_ObjectProxy? proxy = null;

        if (!string.IsNullOrEmpty(componentGuid) && Guid.TryParse(componentGuid, out var guid))
        {
            proxy = Instances.ComponentServer.FindObjectByName(componentName, true, true)
                ?? Instances.ComponentServer.ObjectProxies.FirstOrDefault(p => p.Guid == guid);
        }

        if (proxy == null && !string.IsNullOrEmpty(componentName))
        {
            // Search by name (case-insensitive)
            proxy = Instances.ComponentServer.FindObjectByName(componentName, true, true);

            // If not found, try partial match
            if (proxy == null)
            {
                proxy = Instances.ComponentServer.ObjectProxies
                    .FirstOrDefault(p => p.Desc.Name.Contains(componentName, StringComparison.OrdinalIgnoreCase));
            }
        }

        if (proxy == null)
        {
            throw new InvalidOperationException($"Component '{componentName ?? componentGuid}' not found. Use search_gh_components to find valid component names.");
        }

        // Create the component instance
        var obj = proxy.CreateInstance();
        if (obj == null)
        {
            throw new InvalidOperationException($"Failed to create instance of component '{proxy.Desc.Name}'");
        }

        // Set nickname if provided
        if (!string.IsNullOrEmpty(nickname))
        {
            obj.NickName = nickname;
        }

        // Set position
        obj.Attributes.Pivot = position;

        // Add to document
        doc.AddObject(obj, false);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["category"] = obj.Category,
            ["position"] = new JArray { position.X, position.Y },
            ["message"] = $"Added component '{obj.Name}' to canvas"
        };
    }
}
