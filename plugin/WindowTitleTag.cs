using System;
using System.Runtime.InteropServices;
using System.Text;
using Rhino;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// Prefixes the Rhino main window title with "[MCP:port] " so that, with
    /// several Rhino instances open, you can tell which one an MCP client talks
    /// to (also in the taskbar, which shows the start of the title). Rhino
    /// rewrites the title when a document is opened, saved or renamed, so the
    /// tag is re-applied on Idle. Windows only: on macOS each document has its
    /// own window and the port is shown by mcpstatus instead.
    /// </summary>
    static class WindowTitleTag
    {
        private const int WM_MDIGETACTIVE = 0x0229;

        private static string tag;

        public static void Show(string text)
        {
            if (!OperatingSystem.IsWindows()) return;

            Clear();
            tag = $"[{text}] ";
            Apply();
            RhinoApp.Idle += OnIdle;
        }

        public static void Clear()
        {
            if (tag == null) return;

            RhinoApp.Idle -= OnIdle;
            IntPtr hwnd = RhinoApp.MainWindowHandle();
            if (hwnd != IntPtr.Zero)
            {
                string title = FrameTitle(hwnd);
                if (title.StartsWith(tag, StringComparison.Ordinal))
                {
                    SetWindowTextW(hwnd, title.Substring(tag.Length));
                }
            }
            tag = null;
        }

        private static void OnIdle(object sender, EventArgs e) => Apply();

        private static void Apply()
        {
            IntPtr hwnd = RhinoApp.MainWindowHandle();
            if (tag == null || hwnd == IntPtr.Zero) return;

            string title = FrameTitle(hwnd);
            if (!title.StartsWith(tag, StringComparison.Ordinal))
            {
                SetWindowTextW(hwnd, tag + title);
            }
        }

        /// <summary>
        /// The frame's own title. Rhino's main window is an MDI frame, and while
        /// the view child is maximized Windows displays "title - [view]"; setting
        /// that displayed text back would make Windows append " - [view]" again
        /// on every update, so the suffix is removed first.
        /// </summary>
        private static string FrameTitle(IntPtr hwnd)
        {
            string title = GetTitle(hwnd);
            IntPtr mdiClient = FindWindowExW(hwnd, IntPtr.Zero, "MDIClient", null);
            if (mdiClient == IntPtr.Zero) return title;

            IntPtr child = SendMessageW(mdiClient, WM_MDIGETACTIVE, IntPtr.Zero, out int maximized);
            if (child == IntPtr.Zero || maximized == 0) return title;

            string suffix = $" - [{GetTitle(child)}]";
            return title.EndsWith(suffix, StringComparison.Ordinal)
                ? title.Substring(0, title.Length - suffix.Length)
                : title;
        }

        private static string GetTitle(IntPtr hwnd)
        {
            int length = GetWindowTextLengthW(hwnd);
            if (length <= 0) return string.Empty;
            var buffer = new StringBuilder(length + 1);
            GetWindowTextW(hwnd, buffer, buffer.Capacity);
            return buffer.ToString();
        }

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowTextLengthW(IntPtr hWnd);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowTextW(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern bool SetWindowTextW(IntPtr hWnd, string lpString);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern IntPtr FindWindowExW(IntPtr hWndParent, IntPtr hWndChildAfter, string lpszClass, string lpszWindow);

        [DllImport("user32.dll")]
        private static extern IntPtr SendMessageW(IntPtr hWnd, int msg, IntPtr wParam, out int lParam);
    }
}
