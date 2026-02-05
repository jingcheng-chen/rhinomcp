using System;
using Grasshopper;
using Grasshopper.Kernel;

namespace GrasshopperMCPPlugin;

/// <summary>
/// Grasshopper Assembly Priority loader for the MCP plugin.
/// This ensures the plugin loads when Grasshopper starts.
/// </summary>
public class GrasshopperMCPPluginInfo : GH_AssemblyInfo
{
    public override string Name => "GrasshopperMCP";
    public override string Description => "Grasshopper integration through the Model Context Protocol";
    public override Guid Id => new Guid("A1B2C3D4-E5F6-7890-ABCD-EF1234567890");
    public override string AuthorName => "Jingcheng Chen";
    public override string AuthorContact => "";
    public override string Version => "0.1.0";
}

/// <summary>
/// Static class to manage the GrasshopperMCP server instance.
/// </summary>
public static class GrasshopperMCPServerController
{
    private static GrasshopperMCPServer? _server;
    private static readonly object _lock = new object();

    /// <summary>
    /// Start the GrasshopperMCP server.
    /// </summary>
    public static void Start(string host = "127.0.0.1", int port = 2000)
    {
        lock (_lock)
        {
            if (_server != null && _server.IsRunning())
            {
                Rhino.RhinoApp.WriteLine("GrasshopperMCP server is already running");
                return;
            }

            _server = new GrasshopperMCPServer(host, port);
            _server.Start();
        }
    }

    /// <summary>
    /// Stop the GrasshopperMCP server.
    /// </summary>
    public static void Stop()
    {
        lock (_lock)
        {
            if (_server != null)
            {
                _server.Stop();
                _server = null;
            }
        }
    }

    /// <summary>
    /// Check if the server is running.
    /// </summary>
    public static bool IsRunning()
    {
        lock (_lock)
        {
            return _server != null && _server.IsRunning();
        }
    }
}
