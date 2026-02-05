using Rhino;
using Rhino.Commands;

namespace GrasshopperMCPPlugin.Commands;

/// <summary>
/// Command to stop the GrasshopperMCP server.
/// </summary>
public class GHMCPStopCommand : Command
{
    public override string EnglishName => "GHMCPStop";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        if (!GrasshopperMCPServerController.IsRunning())
        {
            RhinoApp.WriteLine("GrasshopperMCP server is not running");
            return Result.Nothing;
        }

        GrasshopperMCPServerController.Stop();
        return Result.Success;
    }
}
