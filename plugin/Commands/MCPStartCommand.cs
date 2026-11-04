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
    public class MCPStartCommand : Command
    {
        public MCPStartCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPStartCommand Instance { get; private set; }

        

        public override string EnglishName => "mcpstart";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Plain "mcpstart" never prompts, so it keeps working from startup
            // scripts (/runscript="_mcpstart"). The dashed form asks for a port:
            //   _-mcpstart 2000      or      _-mcpstart _Port=2000 _Enter
            // 0 (the default) means RHINO_MCP_PORT, else the first free port
            // from 1999.
            int port = 0;
            if (mode == RunMode.Scripted)
            {
                var portOption = new OptionInteger(0, 0, 65535);
                var go = new GetOption();
                go.SetCommandPrompt("RhinoMCP port (0 = automatic)");
                go.AcceptNothing(true);
                go.AcceptNumber(true, true);
                go.AddOptionInteger("Port", ref portOption);
                while (true)
                {
                    GetResult res = go.Get();
                    if (res == GetResult.Option)
                    {
                        continue;
                    }
                    if (res == GetResult.Number)
                    {
                        double number = go.Number();
                        if (number < 0 || number > 65535 || number != Math.Floor(number))
                        {
                            RhinoApp.WriteLine($"{number} is not a valid port.");
                            return Result.Failure;
                        }
                        port = (int)number;
                        break;
                    }
                    if (res == GetResult.Nothing)
                    {
                        port = portOption.CurrentValue;
                        break;
                    }
                    return Result.Cancel;
                }
            }

            return RhinoMCPServerController.StartServer(port) ? Result.Success : Result.Failure;
        }

    }
}
