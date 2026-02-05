using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Get detailed information about a specific component.
    /// </summary>
    public JObject GetComponentInfo(JObject parameters)
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

        var result = new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["category"] = obj.Category,
            ["subcategory"] = obj.SubCategory,
            ["description"] = obj.Description,
            ["position"] = new JArray { obj.Attributes.Pivot.X, obj.Attributes.Pivot.Y },
            ["type"] = obj.GetType().Name
        };

        // Add component-specific info
        if (obj is IGH_Component component)
        {
            result["runtime_message_level"] = component.RuntimeMessageLevel.ToString();
            result["is_obsolete"] = component.Obsolete;

            // Input parameters
            var inputs = new JArray();
            foreach (var input in component.Params.Input)
            {
                var inputInfo = new JObject
                {
                    ["name"] = input.Name,
                    ["nickname"] = input.NickName,
                    ["description"] = input.Description,
                    ["type"] = input.TypeName,
                    ["access"] = input.Access.ToString(),
                    ["optional"] = input.Optional,
                    ["source_count"] = input.SourceCount,
                    ["has_data"] = input.VolatileDataCount > 0
                };
                inputs.Add(inputInfo);
            }
            result["inputs"] = inputs;

            // Output parameters
            var outputs = new JArray();
            foreach (var output in component.Params.Output)
            {
                var outputInfo = new JObject
                {
                    ["name"] = output.Name,
                    ["nickname"] = output.NickName,
                    ["description"] = output.Description,
                    ["type"] = output.TypeName,
                    ["recipient_count"] = output.Recipients.Count,
                    ["has_data"] = output.VolatileDataCount > 0
                };
                outputs.Add(outputInfo);
            }
            result["outputs"] = outputs;

            // Runtime messages
            var messages = new JArray();
            foreach (var msg in component.RuntimeMessages(GH_RuntimeMessageLevel.Blank))
            {
                messages.Add(msg);
            }
            result["runtime_messages"] = messages;
        }
        else if (obj is IGH_Param param)
        {
            result["type_name"] = param.TypeName;
            result["source_count"] = param.SourceCount;
            result["recipient_count"] = param.Recipients.Count;
            result["data_count"] = param.VolatileDataCount;
        }

        return result;
    }
}
