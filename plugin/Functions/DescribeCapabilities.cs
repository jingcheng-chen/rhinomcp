using System;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Self-description of what this MCP server can do: every command it handles
    /// and whether that command is read-only, plus the perception envelope flags
    /// it honors and the plugin version. Read-only.
    ///
    /// This is distinct from get_commands, which lists Rhino's own application
    /// commands (Box, Circle, ...) for use with run_command. describe_capabilities
    /// lists the MCP command surface itself, so an agent can discover what it can
    /// send instead of guessing. The command list is the live dispatch table
    /// (GetDispatchTable), so it never drifts from what the server actually
    /// accepts: add a [McpCommand] and it appears here automatically.
    ///
    /// Parameters are deliberately not included. The handlers take an untyped
    /// JObject, so there is no parameter schema to reflect at runtime; the
    /// authoritative parameter shapes live in the contracts/ schemas and are
    /// already surfaced to clients through the MCP tool list.
    /// </summary>
    [McpCommand("describe_capabilities", ReadOnly = true)]
    public JObject DescribeCapabilities(JObject parameters)
    {
        var table = GetDispatchTable();

        var commands = new JArray();
        foreach (var name in table.Keys.OrderBy(n => n, StringComparer.Ordinal))
        {
            commands.Add(new JObject
            {
                ["name"] = name,
                ["read_only"] = table[name].ReadOnly
            });
        }

        // Opt-in envelope flags the dispatcher honors (see ExecuteCommandInternal).
        // Each attaches an extra feedback block to a mutating command's result.
        var envelopeFlags = new JArray
        {
            new JObject
            {
                ["flag"] = "include_delta",
                ["attaches"] = "_delta",
                ["description"] = "Attaches a change-delta (created/deleted ids and counts) to a mutating command's result."
            },
            new JObject
            {
                ["flag"] = "include_health",
                ["attaches"] = "_health",
                ["description"] = "Attaches a geometry-health report (created/modified objects that fail validity checks, with reasons) to a mutating command's result."
            }
        };

        return new JObject
        {
            ["version"] = GetPluginVersion(),
            ["command_count"] = commands.Count,
            ["commands"] = commands,
            ["perception"] = new JObject
            {
                ["description"] = "Mutating commands accept opt-in envelope flags that attach extra feedback to the result. Set them per command on the envelope, or globally with the RHINO_MCP_PERCEPTION server setting.",
                ["envelope_flags"] = envelopeFlags
            }
        };
    }

    /// <summary>Plugin version without the build-metadata (+commit) suffix.</summary>
    private static string GetPluginVersion()
    {
        var asm = typeof(RhinoMCPFunctions).Assembly;
        var info = asm.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
        if (!string.IsNullOrEmpty(info))
        {
            int plus = info.IndexOf('+');
            return plus >= 0 ? info.Substring(0, plus) : info;
        }
        return asm.GetName().Version?.ToString() ?? "unknown";
    }
}
