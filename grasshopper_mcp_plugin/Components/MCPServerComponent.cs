using System;
using System.Collections.Generic;
using Grasshopper.Kernel;

namespace GrasshopperMCPPlugin.Components;

/// <summary>
/// Grasshopper component to control the MCP server.
/// Place this component on the canvas to start the server.
/// </summary>
public class MCPServerComponent : GH_Component
{
    private bool _wasRunning = false;
    private int _lastLogCount = 0;

    public MCPServerComponent()
        : base(
            "MCP Server",
            "MCP",
            "Start/Stop the GrasshopperMCP server for AI agent communication",
            "Params",
            "Util")
    {
        // Subscribe to log updates
        MCPLogger.OnLogAdded += OnLogAdded;
    }

    ~MCPServerComponent()
    {
        MCPLogger.OnLogAdded -= OnLogAdded;
    }

    private void OnLogAdded()
    {
        // Schedule a solution expiration to update the output
        // This runs on the UI thread
        Rhino.RhinoApp.InvokeOnUiThread((Action)(() =>
        {
            ExpireSolution(true);
        }));
    }

    public override Guid ComponentGuid => new Guid("F1E2D3C4-B5A6-7890-1234-567890ABCDEF");

    protected override void RegisterInputParams(GH_InputParamManager pManager)
    {
        pManager.AddBooleanParameter("Start", "S", "Set to true to start the server, false to stop", GH_ParamAccess.item, true);
        pManager.AddIntegerParameter("Port", "P", "Port number for the server (default: 2000)", GH_ParamAccess.item, 2000);
        pManager.AddBooleanParameter("Clear Logs", "C", "Set to true to clear the log history", GH_ParamAccess.item, false);
    }

    protected override void RegisterOutputParams(GH_OutputParamManager pManager)
    {
        pManager.AddBooleanParameter("Running", "R", "True if the server is currently running", GH_ParamAccess.item);
        pManager.AddTextParameter("Status", "S", "Server status message", GH_ParamAccess.item);
        pManager.AddTextParameter("Logs", "L", "Server activity logs", GH_ParamAccess.list);
    }

    protected override void SolveInstance(IGH_DataAccess DA)
    {
        bool start = true;
        int port = 2000;
        bool clearLogs = false;

        DA.GetData(0, ref start);
        DA.GetData(1, ref port);
        DA.GetData(2, ref clearLogs);

        // Clear logs if requested
        if (clearLogs)
        {
            MCPLogger.Clear();
        }

        if (port < 1024 || port > 65535)
        {
            AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Port must be between 1024 and 65535");
            DA.SetData(0, false);
            DA.SetData(1, "Invalid port number");
            DA.SetDataList(2, new List<string>());
            return;
        }

        bool isRunning = GrasshopperMCPServerController.IsRunning();
        string status;

        if (start && !isRunning)
        {
            // Start the server
            try
            {
                GrasshopperMCPServerController.Start("127.0.0.1", port);
                isRunning = GrasshopperMCPServerController.IsRunning();
                status = isRunning
                    ? $"Server running on port {port}"
                    : "Failed to start server";
            }
            catch (Exception ex)
            {
                status = $"Error: {ex.Message}";
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, ex.Message);
            }
        }
        else if (!start && isRunning)
        {
            // Stop the server
            GrasshopperMCPServerController.Stop();
            isRunning = GrasshopperMCPServerController.IsRunning();
            status = "Server stopped";
        }
        else if (start && isRunning)
        {
            status = $"Server running on port {port}";
        }
        else
        {
            status = "Server not running";
        }

        // Update component appearance based on state
        if (isRunning != _wasRunning)
        {
            _wasRunning = isRunning;
            Message = isRunning ? "Running" : "Stopped";
        }

        // Get logs
        List<string> logs = MCPLogger.GetLogs();

        DA.SetData(0, isRunning);
        DA.SetData(1, status);
        DA.SetDataList(2, logs);
    }
}
