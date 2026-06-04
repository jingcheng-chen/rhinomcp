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
    public class MCPVersionCommand : Command
    {
        public MCPVersionCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPVersionCommand Instance { get; private set; }

        

        public override string EnglishName => "mcpversion";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // get the version of the plugin from the properties of the project file
            var version = System.Reflection.Assembly.GetExecutingAssembly().GetName().Version;
            Rhino.RhinoApp.WriteLine($"RhinoMCPPlugin version {version}");
            return Result.Success;
        }

    }
}
