using Rhino;
using Rhino.Commands;

namespace GrasshopperMCPPlugin.Commands;

/// <summary>
/// Command to start the GrasshopperMCP server.
/// </summary>
public class GHMCPStartCommand : Command
{
    public override string EnglishName => "GHMCPStart";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        int port = 2000;

        // Allow user to specify port
        if (mode == RunMode.Interactive)
        {
            var getPort = new Rhino.Input.Custom.GetInteger();
            getPort.SetCommandPrompt("Port number");
            getPort.SetDefaultInteger(2000);
            getPort.SetLowerLimit(1024, false);
            getPort.SetUpperLimit(65535, false);

            if (getPort.Get() == Rhino.Input.GetResult.Number)
            {
                port = getPort.Number();
            }
        }

        GrasshopperMCPServerController.Start("127.0.0.1", port);
        return Result.Success;
    }
}
