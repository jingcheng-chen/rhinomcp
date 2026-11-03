using System;
using System.Reflection;
using Rhino;
using Rhino.Commands;

namespace RhinoMCPPlugin.Commands
{
    public class MCPStatusCommand : Command
    {
        public MCPStatusCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPStatusCommand Instance { get; private set; }

        public override string EnglishName => "mcpstatus";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            var assembly = Assembly.GetExecutingAssembly();
            string version = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion
                             ?? assembly.GetName().Version?.ToString();

            var server = RhinoMCPServerController.Server;
            if (server == null)
            {
                RhinoApp.WriteLine($"RhinoMCP {version}: server not running. Start it with mcpstart (or -mcpstart Port=<n>).");
                return Result.Success;
            }

            string docName = string.IsNullOrEmpty(doc?.Name) ? "Untitled" : doc.Name;
            string docPath = string.IsNullOrEmpty(doc?.Path) ? "not saved" : doc.Path;
            var clients = server.ConnectedClients();

            RhinoApp.WriteLine($"RhinoMCP {version}: listening on {server.Host}:{server.Port} " +
                               $"({RhinoMCPServerController.PortSource}, since {server.StartedAt:HH:mm:ss}).");
            RhinoApp.WriteLine($"  Document: {docName} ({docPath})");
            RhinoApp.WriteLine(clients.Count == 0
                ? "  Connected clients: none"
                : $"  Connected clients: {clients.Count}");
            foreach (var c in clients)
            {
                string last = c.LastCommand == null ? "" : $", last {c.LastCommand} at {c.LastCommandAt:HH:mm:ss}";
                RhinoApp.WriteLine($"    {c.Description}: connected {c.ConnectedAt:HH:mm}, {c.CommandCount} commands{last}");
            }
            RhinoApp.WriteLine($"  MCP client setting: {RhinoMCPServerController.PortEnvironmentVariable}={server.Port}");
            return Result.Success;
        }
    }
}
