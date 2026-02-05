using System;
using System.Linq;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

/// <summary>
/// Helper methods for finding components and extracting parameters.
/// Supports both Python-style and C#-style parameter names.
/// </summary>
public static class ComponentHelper
{
    /// <summary>
    /// Find a component by instance_id (GUID) or nickname.
    /// Supports both Python naming (instance_id, nickname) and C# naming (component_id).
    /// </summary>
    public static IGH_DocumentObject FindComponent(GH_Document doc, JObject parameters, string idParamPrefix = "")
    {
        // Support multiple parameter naming conventions
        var instanceId = parameters[$"{idParamPrefix}instance_id"]?.ToString()
                      ?? parameters[$"{idParamPrefix}id"]?.ToString()
                      ?? parameters[$"component_id"]?.ToString();

        var nickname = parameters[$"{idParamPrefix}nickname"]?.ToString();

        if (string.IsNullOrEmpty(instanceId) && string.IsNullOrEmpty(nickname))
        {
            throw new ArgumentException($"Either {idParamPrefix}instance_id or {idParamPrefix}nickname is required");
        }

        IGH_DocumentObject? obj = null;

        // Try finding by GUID first
        if (!string.IsNullOrEmpty(instanceId))
        {
            if (Guid.TryParse(instanceId, out var guid))
            {
                obj = doc.FindObject(guid, true);
            }
            else
            {
                throw new ArgumentException($"Invalid GUID format: {instanceId}");
            }
        }

        // If not found by GUID, try finding by nickname
        if (obj == null && !string.IsNullOrEmpty(nickname))
        {
            obj = doc.Objects.FirstOrDefault(o =>
                o.NickName.Equals(nickname, StringComparison.OrdinalIgnoreCase));
        }

        if (obj == null)
        {
            var identifier = !string.IsNullOrEmpty(instanceId) ? instanceId : nickname;
            throw new InvalidOperationException($"Component '{identifier}' not found");
        }

        return obj;
    }

    /// <summary>
    /// Get parameter index from parameters object.
    /// Supports: output_index, input_index, param_index, source_output, target_input
    /// </summary>
    public static int? GetParamIndex(JObject parameters, bool isOutput, string prefix = "")
    {
        // Try various naming conventions
        if (isOutput)
        {
            return parameters[$"{prefix}output_index"]?.ToObject<int?>()
                ?? parameters[$"{prefix}output"]?.ToObject<int?>()
                ?? parameters["param_index"]?.ToObject<int?>()
                ?? parameters[$"{prefix}param_index"]?.ToObject<int?>();
        }
        else
        {
            return parameters[$"{prefix}input_index"]?.ToObject<int?>()
                ?? parameters[$"{prefix}input"]?.ToObject<int?>()
                ?? parameters["param_index"]?.ToObject<int?>()
                ?? parameters[$"{prefix}param_index"]?.ToObject<int?>();
        }
    }

    /// <summary>
    /// Get parameter name from parameters object.
    /// Supports: output_name, input_name, param_name
    /// </summary>
    public static string? GetParamName(JObject parameters, bool isOutput, string prefix = "")
    {
        if (isOutput)
        {
            return parameters[$"{prefix}output_name"]?.ToString()
                ?? parameters[$"{prefix}param"]?.ToString()
                ?? parameters["param_name"]?.ToString();
        }
        else
        {
            return parameters[$"{prefix}input_name"]?.ToString()
                ?? parameters[$"{prefix}param"]?.ToString()
                ?? parameters["param_name"]?.ToString();
        }
    }

    /// <summary>
    /// Find output parameter on a component.
    /// </summary>
    public static IGH_Param? FindOutputParam(IGH_DocumentObject obj, int? paramIndex, string? paramName)
    {
        if (obj is IGH_Component component)
        {
            if (paramIndex.HasValue && paramIndex.Value < component.Params.Output.Count)
            {
                return component.Params.Output[paramIndex.Value];
            }
            else if (!string.IsNullOrEmpty(paramName))
            {
                return component.Params.Output
                    .FirstOrDefault(p => p.Name.Equals(paramName, StringComparison.OrdinalIgnoreCase)
                                      || p.NickName.Equals(paramName, StringComparison.OrdinalIgnoreCase));
            }
            else if (component.Params.Output.Count == 1)
            {
                return component.Params.Output[0];
            }
            else if (component.Params.Output.Count > 0)
            {
                // Default to first output
                return component.Params.Output[0];
            }
        }
        else if (obj is IGH_Param param)
        {
            return param;
        }

        return null;
    }

    /// <summary>
    /// Find input parameter on a component.
    /// </summary>
    public static IGH_Param? FindInputParam(IGH_DocumentObject obj, int? paramIndex, string? paramName)
    {
        if (obj is IGH_Component component)
        {
            if (paramIndex.HasValue && paramIndex.Value < component.Params.Input.Count)
            {
                return component.Params.Input[paramIndex.Value];
            }
            else if (!string.IsNullOrEmpty(paramName))
            {
                return component.Params.Input
                    .FirstOrDefault(p => p.Name.Equals(paramName, StringComparison.OrdinalIgnoreCase)
                                      || p.NickName.Equals(paramName, StringComparison.OrdinalIgnoreCase));
            }
            else if (component.Params.Input.Count == 1)
            {
                return component.Params.Input[0];
            }
            else if (component.Params.Input.Count > 0)
            {
                // Default to first input
                return component.Params.Input[0];
            }
        }
        else if (obj is IGH_Param param)
        {
            return param;
        }

        return null;
    }
}
