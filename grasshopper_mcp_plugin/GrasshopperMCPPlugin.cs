using System;
using System.Collections.Generic;
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
/// Static class to manage logs from the MCP server.
/// </summary>
public static class MCPLogger
{
    private static readonly object _lock = new object();
    private static readonly Queue<string> _logs = new Queue<string>();
    private const int MaxLogEntries = 100;

    /// <summary>
    /// Event fired when a new log entry is added.
    /// </summary>
    public static event Action? OnLogAdded;

    /// <summary>
    /// Add a log entry with timestamp.
    /// </summary>
    public static void Log(string message)
    {
        lock (_lock)
        {
            string entry = $"[{DateTime.Now:HH:mm:ss}] {message}";
            _logs.Enqueue(entry);

            // Keep only the last N entries
            while (_logs.Count > MaxLogEntries)
            {
                _logs.Dequeue();
            }
        }

        // Also write to Rhino command line
        Rhino.RhinoApp.WriteLine($"GrasshopperMCP: {message}");

        // Notify listeners
        OnLogAdded?.Invoke();
    }

    /// <summary>
    /// Get all current log entries.
    /// </summary>
    public static List<string> GetLogs()
    {
        lock (_lock)
        {
            return new List<string>(_logs);
        }
    }

    /// <summary>
    /// Clear all logs.
    /// </summary>
    public static void Clear()
    {
        lock (_lock)
        {
            _logs.Clear();
        }
    }
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
                MCPLogger.Log("Server is already running");
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
