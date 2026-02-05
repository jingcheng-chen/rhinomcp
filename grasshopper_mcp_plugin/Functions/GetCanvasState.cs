using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Get the current state of the Grasshopper canvas including all connections.
    /// </summary>
    public JObject GetCanvasState(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var includeConnections = parameters["include_connections"]?.ToObject<bool>() ?? true;
        var includeValues = parameters["include_values"]?.ToObject<bool>() ?? false;

        var result = new JObject();

        // Document info
        result["file_path"] = doc.FilePath ?? "(unsaved)";
        result["object_count"] = doc.ObjectCount;

        // Components
        var components = new JArray();
        foreach (var comp in doc.Objects.OfType<IGH_Component>())
        {
            var compInfo = new JObject
            {
                ["instance_id"] = comp.InstanceGuid.ToString(),
                ["name"] = comp.Name,
                ["nickname"] = comp.NickName,
                ["category"] = comp.Category,
                ["position"] = new JArray { comp.Attributes.Pivot.X, comp.Attributes.Pivot.Y },
                ["runtime_state"] = comp.RuntimeMessageLevel.ToString()
            };

            // Input params
            var inputs = new JArray();
            foreach (var input in comp.Params.Input)
            {
                var inputInfo = new JObject
                {
                    ["name"] = input.Name,
                    ["nickname"] = input.NickName,
                    ["source_count"] = input.SourceCount
                };

                if (includeConnections && input.SourceCount > 0)
                {
                    var sources = new JArray();
                    foreach (var source in input.Sources)
                    {
                        sources.Add(new JObject
                        {
                            ["component_id"] = source.Attributes.GetTopLevel.DocObject.InstanceGuid.ToString(),
                            ["param_name"] = source.Name
                        });
                    }
                    inputInfo["sources"] = sources;
                }

                inputs.Add(inputInfo);
            }
            compInfo["inputs"] = inputs;

            // Output params
            var outputs = new JArray();
            foreach (var output in comp.Params.Output)
            {
                var outputInfo = new JObject
                {
                    ["name"] = output.Name,
                    ["nickname"] = output.NickName,
                    ["recipient_count"] = output.Recipients.Count
                };

                if (includeConnections && output.Recipients.Count > 0)
                {
                    var recipients = new JArray();
                    foreach (var recipient in output.Recipients)
                    {
                        recipients.Add(new JObject
                        {
                            ["component_id"] = recipient.Attributes.GetTopLevel.DocObject.InstanceGuid.ToString(),
                            ["param_name"] = recipient.Name
                        });
                    }
                    outputInfo["recipients"] = recipients;
                }

                outputs.Add(outputInfo);
            }
            compInfo["outputs"] = outputs;

            components.Add(compInfo);
        }
        result["components"] = components;

        // Standalone parameters
        var standaloneParams = new JArray();
        foreach (var param in doc.Objects.OfType<IGH_Param>().Where(p => !(p is IGH_Component)))
        {
            // Skip if it's part of a component
            if (param.Attributes.GetTopLevel.DocObject is IGH_Component)
                continue;

            var paramInfo = new JObject
            {
                ["instance_id"] = param.InstanceGuid.ToString(),
                ["name"] = param.Name,
                ["nickname"] = param.NickName,
                ["type"] = param.TypeName,
                ["position"] = new JArray { param.Attributes.Pivot.X, param.Attributes.Pivot.Y }
            };

            standaloneParams.Add(paramInfo);
        }
        result["standalone_parameters"] = standaloneParams;

        // Groups
        var groups = new JArray();
        foreach (var group in doc.Objects.OfType<GH_Group>())
        {
            var groupInfo = new JObject
            {
                ["instance_id"] = group.InstanceGuid.ToString(),
                ["nickname"] = group.NickName,
                ["object_count"] = group.ObjectIDs.Count
            };
            groups.Add(groupInfo);
        }
        result["groups"] = groups;

        return result;
    }
}
