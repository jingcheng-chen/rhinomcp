using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Disconnect a wire between two components.
    /// Supports both Python naming (source_instance_id, source_nickname, source_output)
    /// and C# naming (source_id, source_param).
    /// </summary>
    public JObject DisconnectComponents(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Option to disconnect all sources from a target
        var disconnectAll = parameters["disconnect_all"]?.ToObject<bool>() ?? false;

        // Find target component (required)
        var targetObj = ComponentHelper.FindComponent(doc, parameters, "target_");

        // Get target input parameter
        var targetParamIndex = ComponentHelper.GetParamIndex(parameters, isOutput: false, "target_");
        var targetParamName = ComponentHelper.GetParamName(parameters, isOutput: false, "target_");

        var inputParam = ComponentHelper.FindInputParam(targetObj, targetParamIndex, targetParamName);
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on target component '{targetObj.NickName}'");
        }

        int disconnectedCount = 0;

        if (disconnectAll)
        {
            // Disconnect all sources
            disconnectedCount = inputParam.SourceCount;
            inputParam.RemoveAllSources();
        }
        else
        {
            // Find and disconnect specific source
            // Check if source is specified
            var sourceInstanceId = parameters["source_instance_id"]?.ToString()
                                ?? parameters["source_id"]?.ToString();
            var sourceNickname = parameters["source_nickname"]?.ToString();

            if (string.IsNullOrEmpty(sourceInstanceId) && string.IsNullOrEmpty(sourceNickname))
            {
                throw new ArgumentException("Either source_instance_id/source_nickname or disconnect_all=true is required");
            }

            var sourceObj = ComponentHelper.FindComponent(doc, parameters, "source_");

            // Get source output parameter
            var sourceParamIndex = ComponentHelper.GetParamIndex(parameters, isOutput: true, "source_");
            var sourceParamName = ComponentHelper.GetParamName(parameters, isOutput: true, "source_");

            var outputParam = ComponentHelper.FindOutputParam(sourceObj, sourceParamIndex, sourceParamName);

            if (outputParam != null && inputParam.Sources.Contains(outputParam))
            {
                inputParam.RemoveSource(outputParam);
                disconnectedCount = 1;
            }
        }

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["target_id"] = targetObj.InstanceGuid.ToString(),
            ["target_nickname"] = targetObj.NickName,
            ["target_param"] = inputParam.Name,
            ["disconnected_count"] = disconnectedCount,
            ["message"] = disconnectedCount > 0
                ? $"Disconnected {disconnectedCount} connection(s) from {targetObj.NickName}.{inputParam.Name}"
                : "No connections were disconnected"
        };
    }
}
