using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Commands;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using System.ComponentModel;
using System.Threading.Tasks;

namespace RhinoMCPPlugin.Commands
{
    public class MCPStopCommand : Command
    {
        public MCPStopCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPStopCommand Instance { get; private set; }

        

        public override string EnglishName => "mcpstop";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            RhinoMCPServerController.StopServer();
            return Result.Success;
        }

    }
}
