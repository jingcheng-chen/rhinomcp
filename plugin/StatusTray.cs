using System;
using System.Diagnostics;
using System.IO;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// Starts RhinoMCPTray.exe, shipped next to the plug-in: one tray icon and
    /// window for all running Rhino instances. A second launch only signals the
    /// running copy, so every Rhino can call this.
    /// </summary>
    static class StatusTray
    {
        private const string ExeName = "RhinoMCPTray.exe";

        public static string ExePath =>
            Path.Combine(Path.GetDirectoryName(typeof(StatusTray).Assembly.Location) ?? "", ExeName);

        /// <returns>false on macOS, or when the exe is missing or cannot start.</returns>
        public static bool Launch(bool showWindow)
        {
            if (!OperatingSystem.IsWindows() || !File.Exists(ExePath)) return false;
            try
            {
                var start = new ProcessStartInfo(ExePath, showWindow ? "--show" : "")
                {
                    UseShellExecute = false,
                    WorkingDirectory = Path.GetDirectoryName(ExePath),
                };
                // Rhino's port settings must not leak into the shared tray app.
                start.Environment.Remove(RhinoMCPServerController.PortEnvironmentVariable);
                Process.Start(start)?.Dispose();
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}
