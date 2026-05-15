using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Rhino;

namespace RhinoMCPPlugin
{
    class RhinoMCPServerController
    {
        private static RhinoMCPServer server;

        public static void StartServer()
        {
            if (server == null)
            {
                server = new RhinoMCPServer();
            }

            server.Start();
            RhinoApp.WriteLine("Server started.");
        }

        public static void StopServer()
        {
            if (server != null)
            {
                server.Stop();
                server = null;
                RhinoApp.WriteLine("Server stopped.");
            }
        }

        public static bool IsServerRunning()
        {
            // Used by mcpversion / status — must reflect actual state, not just
            // whether the controller has ever started a server. A Stop() leaves
            // server null, but a server that failed mid-start may have running=false
            // while server is non-null.
            return server != null && server.IsRunning();
        }
    }
}
