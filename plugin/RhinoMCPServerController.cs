using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Rhino;

namespace RhinoMCPPlugin
{
    class RhinoMCPServerController
    {
        public const string DefaultHost = "127.0.0.1";
        // Without an explicit port, mcpstart takes the first free port in
        // DefaultPort .. DefaultPort + AutoPortCount - 1 (1999-2008), so several
        // Rhino instances can each run a server. The first one still gets 1999,
        // which is what an MCP client without RHINO_MCP_PORT talks to.
        public const int DefaultPort = 1999;
        public const int AutoPortCount = 10;
        // Same variable the Python MCP server reads, so one value can drive both
        // sides when Rhino is launched from a script.
        public const string PortEnvironmentVariable = "RHINO_MCP_PORT";

        private static RhinoMCPServer server;

        /// <summary>How the port of the running server was chosen, for mcpstatus.</summary>
        public static string PortSource { get; private set; }

        public static RhinoMCPServer Server => IsServerRunning() ? server : null;

        /// <param name="requestedPort">Port from the command line, or 0 to use
        /// RHINO_MCP_PORT, or failing that the first free automatic port.</param>
        public static bool StartServer(int requestedPort = 0)
        {
            if (IsServerRunning())
            {
                RhinoApp.WriteLine($"RhinoMCP server is already running on {server.Host}:{server.Port}. Run mcpstop first to change port.");
                return true;
            }

            int[] candidates;
            string source;
            if (requestedPort > 0)
            {
                candidates = new[] { requestedPort };
                source = "Port option";
            }
            else if (TryGetEnvironmentPort(out int environmentPort))
            {
                candidates = new[] { environmentPort };
                source = PortEnvironmentVariable;
            }
            else
            {
                candidates = Enumerable.Range(DefaultPort, AutoPortCount).ToArray();
                source = "automatic";
            }

            var busy = new List<int>();
            foreach (int port in candidates)
            {
                var candidate = new RhinoMCPServer(DefaultHost, port);
                switch (candidate.Start(out string error))
                {
                    case RhinoMCPServer.StartResult.Started:
                        server = candidate;
                        PortSource = source;
                        WindowTitleTag.Show($"MCP:{port}");
                        InstanceStatusFile.Start();
                        StatusTray.Launch(showWindow: false);
                        RhinoApp.WriteLine($"RhinoMCP server started on {DefaultHost}:{port} ({source}).");
                        if (port != DefaultPort)
                        {
                            RhinoApp.WriteLine($"MCP clients must set {PortEnvironmentVariable}={port} to talk to this Rhino.");
                        }
                        return true;

                    case RhinoMCPServer.StartResult.PortUnavailable when candidates.Length > 1:
                        busy.Add(port);
                        continue;

                    case RhinoMCPServer.StartResult.PortUnavailable:
                        RhinoApp.WriteLine($"RhinoMCP server not started: port {port} ({source}) is already in use, probably by another Rhino. " +
                                           $"Run mcpstatus there, or choose another port with: -mcpstart Port=<n>");
                        return false;

                    default:
                        RhinoApp.WriteLine($"RhinoMCP server not started on {DefaultHost}:{port}: {error}");
                        return false;
                }
            }

            RhinoApp.WriteLine($"RhinoMCP server not started: ports {busy.First()}-{busy.Last()} are all in use. " +
                               $"Stop a server with mcpstop in another Rhino, or choose a port with: -mcpstart Port=<n>");
            return false;
        }

        public static void StopServer()
        {
            if (server == null)
            {
                RhinoApp.WriteLine("RhinoMCP server is not running.");
                return;
            }

            int port = server.Port;
            server.Stop();
            server = null;
            PortSource = null;
            WindowTitleTag.Clear();
            InstanceStatusFile.Stop();
            RhinoApp.WriteLine($"RhinoMCP server on port {port} stopped.");
        }

        public static bool IsServerRunning()
        {
            // Used by mcpversion / status — must reflect actual state, not just
            // whether the controller has ever started a server. A Stop() leaves
            // server null, but a server that failed mid-start may have running=false
            // while server is non-null.
            return server != null && server.IsRunning();
        }

        private static bool TryGetEnvironmentPort(out int port)
        {
            port = 0;
            string value = Environment.GetEnvironmentVariable(PortEnvironmentVariable);
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }
            if (int.TryParse(value.Trim(), out port) && port > 0 && port <= 65535)
            {
                return true;
            }
            RhinoApp.WriteLine($"Ignoring {PortEnvironmentVariable}={value}: not a port number.");
            return false;
        }
    }
}
