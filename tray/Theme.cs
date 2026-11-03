using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace RhinoMCPTray
{
    /// <summary>Colours close to the Windows 11 flyouts, light or dark like the taskbar.</summary>
    class Theme
    {
        public Color Background, Card, CardHover, CardBorder, Divider, Text, Secondary, Tertiary,
                     Connected, Listening, PillBack, PillText, Warning;

        public static Theme Current() => TaskbarIsLight() ? Light : Dark;

        private static readonly Theme Dark = new Theme
        {
            Background = Hex(0x202020),
            Card = Hex(0x2B2B2B),
            CardHover = Hex(0x333333),
            CardBorder = Hex(0x383838),
            Divider = Hex(0x3A3A3A),
            Text = Hex(0xF2F2F2),
            Secondary = Hex(0xA8A8A8),
            Tertiary = Hex(0x7C7C7C),
            Connected = Hex(0x6CCB5F),
            Listening = Hex(0x60CDFF),
            PillBack = Hex(0x1F3A48),
            PillText = Hex(0x99DDFF),
            Warning = Hex(0xFCE100),
        };

        private static readonly Theme Light = new Theme
        {
            Background = Hex(0xF3F3F3),
            Card = Hex(0xFFFFFF),
            CardHover = Hex(0xF8F8F8),
            CardBorder = Hex(0xE5E5E5),
            Divider = Hex(0xEBEBEB),
            Text = Hex(0x1B1B1B),
            Secondary = Hex(0x5E5E5E),
            Tertiary = Hex(0x8A8A8A),
            Connected = Hex(0x0F7B0F),
            Listening = Hex(0x005FB8),
            PillBack = Hex(0xE0EEF9),
            PillText = Hex(0x003E92),
            Warning = Hex(0x9D5D00),
        };

        private static Color Hex(int rgb) => Color.FromArgb(255, (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF);

        private static bool TaskbarIsLight()
        {
            try
            {
                using (var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"))
                {
                    return key?.GetValue("SystemUsesLightTheme") is int value && value != 0;
                }
            }
            catch (Exception)
            {
                return false;
            }
        }

        public static GraphicsPath RoundRect(RectangleF r, float radius)
        {
            float d = radius * 2;
            var path = new GraphicsPath();
            path.AddArc(r.Left, r.Top, d, d, 180, 90);
            path.AddArc(r.Right - d, r.Top, d, d, 270, 90);
            path.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            path.AddArc(r.Left, r.Bottom - d, d, d, 90, 90);
            path.CloseFigure();
            return path;
        }

        /// <summary>The app mark: a plug on a rounded tile (the bridge between
        /// Claude and Rhino), with a green dot when a session is connected.</summary>
        public static void DrawMark(Graphics g, RectangleF r, bool connected, Color badgeRing)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            using (var tile = RoundRect(r, r.Width * 0.24f))
            using (var fill = new LinearGradientBrush(r, Color.FromArgb(0x3D, 0x8B, 0xFD), Color.FromArgb(0x1F, 0x5F, 0xD0), 90f))
            {
                g.FillPath(fill, tile);
            }

            // Plug drawn on a 16-unit grid, pointing up.
            float u = r.Width / 16f;
            RectangleF Box(float x, float y, float w, float h) => new RectangleF(r.Left + x * u, r.Top + y * u, w * u, h * u);
            PointF Pt(float x, float y) => new PointF(r.Left + x * u, r.Top + y * u);
            using (var white = new SolidBrush(Color.White))
            {
                g.FillRectangle(white, Box(5.6f, 2.4f, 1.5f, 3.4f));   // prongs
                g.FillRectangle(white, Box(8.9f, 2.4f, 1.5f, 3.4f));
                using (var body = RoundRect(Box(4.2f, 5.4f, 7.6f, 4.2f), 1.3f * u)) g.FillPath(white, body);
                g.FillPolygon(white, new[] { Pt(5.4f, 9.2f), Pt(10.6f, 9.2f), Pt(9.0f, 11.4f), Pt(7.0f, 11.4f) });
                g.FillRectangle(white, Box(7.25f, 11f, 1.5f, 3.2f));    // cable
            }

            if (connected)
            {
                float size = 6.4f * u;
                var badge = new RectangleF(r.Right - size + 0.6f * u, r.Bottom - size + 0.6f * u, size, size);
                // Cut a ring around the badge: transparent on the tray icon, the
                // window colour inside the popup.
                g.CompositingMode = badgeRing.A == 0 ? CompositingMode.SourceCopy : CompositingMode.SourceOver;
                using (var ring = new SolidBrush(badgeRing)) g.FillEllipse(ring, RectangleF.Inflate(badge, 0.9f * u, 0.9f * u));
                g.CompositingMode = CompositingMode.SourceOver;
                using (var green = new SolidBrush(Color.FromArgb(0x3F, 0xB9, 0x50))) g.FillEllipse(green, badge);
            }
        }

        private static void Dot(Graphics g, PointF c, float radius, Color color)
        {
            using (var brush = new SolidBrush(color))
                g.FillEllipse(brush, c.X - radius, c.Y - radius, radius * 2, radius * 2);
        }

        public static Icon TrayIcon(int size, bool connected)
        {
            using (var bitmap = new Bitmap(size, size))
            {
                using (var g = Graphics.FromImage(bitmap))
                {
                    g.TextRenderingHint = TextRenderingHint.AntiAlias;
                    float inset = size / 16f * 0.5f;
                    DrawMark(g, new RectangleF(inset, inset, size - 2 * inset, size - 2 * inset), connected, Color.Transparent);
                }
                IntPtr handle = bitmap.GetHicon();
                try
                {
                    return (Icon)Icon.FromHandle(handle).Clone();
                }
                finally
                {
                    DestroyIcon(handle);
                }
            }
        }

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr handle);
    }
}
