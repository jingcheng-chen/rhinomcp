using System;
using Rhino;
using Rhino.Commands;

namespace RhinoMCPPlugin.Commands
{
    public class MCPWindowCommand : Command
    {
        public MCPWindowCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPWindowCommand Instance { get; private set; }

        public override string EnglishName => "mcpwindow";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Show the tray window that lists every running Rhino.
            if (StatusTray.Launch(showWindow: true))
                return Result.Success;
            RhinoApp.WriteLine(OperatingSystem.IsWindows()
                ? $"RhinoMCP tray app not found: {StatusTray.ExePath}. Run mcpstatus instead."
                : "The RhinoMCP status window is Windows only. Run mcpstatus instead.");
            return Result.Nothing;
        }
    }
}
