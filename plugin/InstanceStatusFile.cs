using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using Eto.Forms;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// While the server runs, keeps %LOCALAPPDATA%\RhinoMCP\instances\&lt;pid&gt;.json up
    /// to date with this instance's port, documents and connected clients. The
    /// RhinoMCP tray app reads that folder, so one window lists every Rhino.
    /// </summary>
    static class InstanceStatusFile
    {
        public static string Folder => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RhinoMCP", "instances");

        private static UITimer timer;
        private static string path;
        private static string lastJson;
        private static bool closingHooked;

        public static void Start()
        {
            path = Path.Combine(Folder, $"{Environment.ProcessId}.json");
            if (timer == null)
            {
                timer = new UITimer { Interval = 1 };
                timer.Elapsed += (sender, e) => Write();
            }
            if (!closingHooked)
            {
                RhinoApp.Closing += (sender, e) => Stop();
                closingHooked = true;
            }
            lastJson = null;
            Write();
            timer.Start();
        }

        public static void Stop()
        {
            timer?.Stop();
            lastJson = null;
            if (path == null) return;
            try
            {
                File.Delete(path);
            }
            catch (Exception)
            {
                // The tray app drops files whose Rhino is gone anyway.
            }
        }

        private static void Write()
        {
            var server = RhinoMCPServerController.Server;
            if (server == null || path == null) return;

            var doc = RhinoDoc.ActiveDoc;
            var process = Process.GetCurrentProcess();
            var assembly = Assembly.GetExecutingAssembly();
            var status = new JObject
            {
                ["pid"] = process.Id,
                ["processStart"] = process.StartTime.ToUniversalTime().ToString("o"),
                ["version"] = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion,
                ["language"] = RhinoLanguage(),
                ["host"] = server.Host,
                ["port"] = server.Port,
                ["portSource"] = RhinoMCPServerController.PortSource,
                ["startedAt"] = server.StartedAt.ToString("o"),
                ["document"] = string.IsNullOrEmpty(doc?.Name) ? null : doc.Name,
                ["documentPath"] = string.IsNullOrEmpty(doc?.Path) ? null : doc.Path,
                ["grasshopper"] = GrasshopperDocument(),
                ["clients"] = new JArray(server.ConnectedClients().Select(c => new JObject
                {
                    ["description"] = c.Description,
                    ["connectedAt"] = c.ConnectedAt.ToString("o"),
                    ["commands"] = c.CommandCount,
                    ["lastCommand"] = c.LastCommand,
                    ["lastCommandAt"] = c.LastCommandAt?.ToString("o"),
                })),
            };

            string json = status.ToString();
            if (json == lastJson) return;
            try
            {
                Directory.CreateDirectory(Folder);
                string temp = path + ".tmp";
                File.WriteAllText(temp, json);
                File.Move(temp, path, true);
                lastJson = json;
            }
            catch (Exception)
            {
                // Tray app reading at the same moment; retried on the next tick.
            }
        }

        private static string RhinoLanguage()
        {
            try
            {
                return CultureInfo.GetCultureInfo(Rhino.ApplicationSettings.AppearanceSettings.LanguageIdentifier).Name;
            }
            catch (Exception)
            {
                return null;
            }
        }

        // Grasshopper is optional: only look at it once Rhino has loaded it, so
        // this never loads Grasshopper by itself. Null means "not loaded".
        private static bool grasshopperLoaded;

        private static string GrasshopperDocument()
        {
            if (!grasshopperLoaded)
            {
                grasshopperLoaded = AppDomain.CurrentDomain.GetAssemblies().Any(a => a.GetName().Name == "Grasshopper");
                if (!grasshopperLoaded) return null;
            }
            try
            {
                return LoadedGrasshopperDocument();
            }
            catch
            {
                return "";
            }
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        private static string LoadedGrasshopperDocument()
        {
            // "" = Grasshopper loaded, no definition open.
            return Grasshopper.Instances.ActiveCanvas?.Document?.DisplayName ?? "";
        }
    }
}
