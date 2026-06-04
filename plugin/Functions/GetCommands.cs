using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino.Commands;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("get_commands", ReadOnly = true)]
    public JObject GetCommands(JObject parameters)
    {
        bool loadedOnly = parameters["loaded_only"]?.ToObject<bool>() ?? true;
        string filter = parameters["filter"]?.ToString();

        string[] names = Command.GetCommandNames(english: true, loaded: loadedOnly) ?? Array.Empty<string>();

        var ordered = names
            .Where(n => !string.IsNullOrEmpty(n))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(n => n, StringComparer.OrdinalIgnoreCase);

        if (!string.IsNullOrEmpty(filter))
        {
            ordered = ordered
                .Where(n => n.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0)
                .OrderBy(n => n, StringComparer.OrdinalIgnoreCase);
        }

        var array = new JArray();
        foreach (var name in ordered)
        {
            array.Add(name);
        }

        return new JObject
        {
            ["count"] = array.Count,
            ["commands"] = array
        };
    }
}
