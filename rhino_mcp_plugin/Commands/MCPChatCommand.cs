using Rhino;
using Rhino.Commands;
using Rhino.Input.Custom;
using Rhino.UI;
using RhinoMCPPlugin.Chat;
using System.Drawing;
using System.IO;
using System.Reflection;

namespace RhinoMCPPlugin.Commands
{
    public class MCPChatCommand : Command
    {
        public MCPChatCommand()
        {
            Panels.RegisterPanel(PlugIn, typeof(ChatEtoPanel), "Chat", Assembly.GetExecutingAssembly(), "rhinomcp.EmbeddedResources.ChatPanel.ico", PanelType.PerDoc);
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPChatCommand Instance { get; private set; }
        

        public override string EnglishName => "mcpchat";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            var panel_id = ChatEtoPanel.PanelId;
            Panels.OpenPanel(panel_id);
            
            return Result.Success;
        }

    }
}
