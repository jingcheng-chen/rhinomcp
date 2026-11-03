using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace RhinoMCPTray
{
    static class Program
    {
        private const string MutexName = @"Local\RhinoMCPTray";
        private const string ShowEventName = @"Local\RhinoMCPTray.Show";

        /// <summary>
        /// One copy per Windows session. Every Rhino starts this on mcpstart; later
        /// copies exit at once, and with --show (mcpwindow) first ask the running
        /// copy to open its window.
        /// </summary>
        [STAThread]
        static void Main(string[] args)
        {
            bool show = args.Contains("--show");
            using (var mutex = new Mutex(true, MutexName, out bool first))
            using (var showEvent = new EventWaitHandle(false, EventResetMode.AutoReset, ShowEventName))
            {
                if (!first)
                {
                    if (show)
                    {
                        // Pass on the foreground right Rhino gave us, so the popup can take focus.
                        AllowSetForegroundWindow(-1);
                        showEvent.Set();
                    }
                    return;
                }

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new TrayContext(showEvent, show));
                GC.KeepAlive(mutex);
            }
        }

        [DllImport("user32.dll")]
        private static extern bool AllowSetForegroundWindow(int processId);
    }

    class TrayContext : ApplicationContext
    {
        // Leave once no Rhino has run a server for this long.
        private static readonly TimeSpan IdleExit = TimeSpan.FromSeconds(20);

        private readonly NotifyIcon tray;
        private readonly StatusPopup popup = new StatusPopup();
        private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 1000 };
        private readonly RegisteredWaitHandle showWait;
        private List<RhinoInstance> instances = new List<RhinoInstance>();
        private DateTime? emptySince;
        private (int Count, bool Connected)? iconState;

        public TrayContext(EventWaitHandle showEvent, bool showNow)
        {
            var menu = new ContextMenuStrip();
            menu.Items.Add(new ToolStripMenuItem(Strings.Current.ShowInstances, null, (s, e) => ShowPopup()) { Font = new Font(menu.Font, FontStyle.Bold) });
            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add(new ToolStripMenuItem(Strings.Current.CloseIcon, null, (s, e) => Quit()));

            tray = new NotifyIcon { ContextMenuStrip = menu, Text = "RhinoMCP", Visible = true };
            tray.MouseUp += (s, e) =>
            {
                if (e.Button != MouseButtons.Left) return;
                // Clicking the icon first deactivates (and hides) an open popup:
                // treat that click as "close", not "open again".
                if (popup.Visible || Environment.TickCount - popup.LastHidden < 300) popup.HidePopup();
                else ShowPopup();
            };

            _ = popup.Handle; // so BeginInvoke works before the first show
            showWait = ThreadPool.RegisterWaitForSingleObject(showEvent,
                (state, timedOut) => popup.BeginInvoke((Action)ShowPopup), null, Timeout.Infinite, false);

            timer.Tick += (s, e) => Refresh();
            timer.Start();
            Refresh();
            if (showNow) ShowPopup();
        }

        private string menuLanguage;

        private void UpdateMenuTexts()
        {
            if (menuLanguage == Strings.Current.ShowInstances) return;
            menuLanguage = Strings.Current.ShowInstances;
            tray.ContextMenuStrip.Items[0].Text = Strings.Current.ShowInstances;
            tray.ContextMenuStrip.Items[2].Text = Strings.Current.CloseIcon;
            iconState = null; // tooltip text too
        }

        private void ShowPopup()
        {
            Refresh();
            popup.ShowNearTray();
        }

        private void Refresh()
        {
            instances = InstanceDirectory.Read();
            Strings.Use(instances.Select(i => i.Language).FirstOrDefault(l => !string.IsNullOrEmpty(l)));
            UpdateMenuTexts();
            popup.SetInstances(instances);
            if (popup.Visible) popup.Invalidate(); // "2 min ago" keeps moving

            bool connected = instances.Any(i => i.Clients.Count > 0);
            if (iconState != (instances.Count, connected))
            {
                iconState = (instances.Count, connected);
                var old = tray.Icon;
                tray.Icon = Theme.TrayIcon(SystemInformation.SmallIconSize.Width, connected);
                old?.Dispose();

                int sessions = instances.Sum(i => i.Clients.Count);
                string text = instances.Count == 0
                    ? Strings.Current.NoneConnectedTip
                    : $"RhinoMCP: {instances.Count} Rhino · Claude: {Strings.Current.Sessions(sessions)}";
                tray.Text = text.Length > 63 ? text.Substring(0, 63) : text;
            }

            if (instances.Count > 0)
            {
                emptySince = null;
            }
            else if (emptySince == null)
            {
                emptySince = DateTime.Now;
            }
            else if (DateTime.Now - emptySince > IdleExit && !popup.Visible)
            {
                Quit();
            }
        }

        private void Quit()
        {
            timer.Stop();
            showWait.Unregister(null);
            tray.Visible = false;
            tray.Dispose();
            popup.Dispose();
            ExitThread();
        }
    }
}
