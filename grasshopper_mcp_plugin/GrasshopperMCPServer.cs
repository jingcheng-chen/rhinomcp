using System;
using Rhino;
using RhinoMCP.Shared.SocketServer;
using GrasshopperMCPPlugin.Functions;

namespace GrasshopperMCPPlugin;

/// <summary>
/// Grasshopper-specific MCP server implementation.
/// Extends the shared BaseSocketServer with Grasshopper-specific handling.
/// </summary>
public class GrasshopperMCPServer : BaseSocketServer
{
    private readonly GrasshopperMCPFunctions handler;

    public override string ServerName => "GrasshopperMCP";

    public GrasshopperMCPServer(string host = "127.0.0.1", int port = 2000)
        : base(host, port)
    {
        this.handler = new GrasshopperMCPFunctions();
    }

    public override ICommandHandler GetHandler() => handler;

    public override void InvokeOnMainThread(Action action)
    {
        // Grasshopper runs on Rhino's UI thread
        RhinoApp.InvokeOnUiThread(action);
    }

    public override uint BeginUndoRecord(string commandName)
    {
        // Grasshopper operations are tracked through Rhino's undo system
        return RhinoDoc.ActiveDoc.BeginUndoRecord(commandName);
    }

    public override void EndUndoRecord(uint recordId)
    {
        RhinoDoc.ActiveDoc.EndUndoRecord(recordId);
    }
}
