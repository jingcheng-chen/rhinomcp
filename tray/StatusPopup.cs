using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace RhinoMCPTray
{
    /// <summary>
    /// Flyout above the tray icon: one card per Rhino with its port, Claude
    /// entry, documents and connected sessions. Clicking a card brings that
    /// Rhino to the front. Owner-drawn so it looks the same at every DPI and
    /// follows the taskbar's light/dark theme.
    /// </summary>
    class StatusPopup : Form
    {
        // Layout in 96-dpi pixels; scaled by S().
        private const int PopupWidth = 336;
        private const int Edge = 10;        // window edge to cards
        private const int HeaderHeight = 38;
        private const int FooterHeight = 28;
        private const int CardGap = 6;
        private const int CardPadding = 10;
        private const int CardRadius = 7;
        private const int TitleLine = 20;
        private const int TextLine = 17;
        private const int SessionHeight = 34;
        private const int DividerGap = 7;

        private static Strings T => Strings.Current;

        private List<RhinoInstance> instances = new List<RhinoInstance>();
        private readonly List<(Rectangle Bounds, RhinoInstance Instance)> cards = new List<(Rectangle, RhinoInstance)>();
        private int hovered = -1;
        private bool hasOverflow;
        private readonly VScrollBar scrollBar = new VScrollBar { Visible = false };
        private float scale = 1f;
        private Theme theme = Theme.Current();
        private Font titleFont, cardTitleFont, bodyFont, smallFont, smallBoldFont;

        /// <summary>Environment.TickCount when the popup last hid itself.</summary>
        public int LastHidden { get; private set; }

        public StatusPopup()
        {
            Text = "RhinoMCP";
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;
            KeyPreview = true;
            AutoScaleMode = AutoScaleMode.None;
            Controls.Add(scrollBar);
            scrollBar.ValueChanged += (sender, e) =>
            {
                LayoutCards();
                hovered = -1;
                Cursor = Cursors.Default;
                Invalidate();
            };
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer |
                     ControlStyles.UserPaint | ControlStyles.ResizeRedraw, true);
        }

        protected override CreateParams CreateParams
        {
            get
            {
                var cp = base.CreateParams;
                cp.ClassStyle |= 0x00020000; // CS_DROPSHADOW
                cp.ExStyle |= 0x00000080;    // WS_EX_TOOLWINDOW: no Alt+Tab entry
                return cp;
            }
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            // Windows 11 rounded corners; ignored on Windows 10.
            int round = 2; // DWMWCP_ROUND
            DwmSetWindowAttribute(Handle, 33, ref round, sizeof(int));
        }

        public void SetInstances(List<RhinoInstance> list)
        {
            instances = list;
            if (Visible) Relayout(keepBottom: true);
        }

        /// <summary>Shows the popup in the corner of the work area next to the tray.</summary>
        public void ShowNearTray()
        {
            var screen = Screen.FromPoint(Cursor.Position);
            theme = Theme.Current();
            SetScale(MonitorDpi(screen) / 96f);
            int height = MeasureHeight();
            int width = S(PopupWidth);
            int gap = S(Edge);

            Rectangle area = screen.WorkingArea, full = screen.Bounds;
            height = Math.Min(height, area.Height - 2 * gap);
            int x = area.Left > full.Left ? area.Left + gap : area.Right - width - gap;   // taskbar on the left?
            int y = area.Top > full.Top ? area.Top + gap : area.Bottom - height - gap;    // taskbar at the top?
            Bounds = new Rectangle(x, y, width, height);
            LayoutCards();

            hovered = -1;
            Show();
            Activate();
        }

        private void Relayout(bool keepBottom)
        {
            int bottom = Bottom;
            var area = Screen.FromControl(this).WorkingArea;
            int height = Math.Min(MeasureHeight(), area.Height - 2 * S(Edge));
            if (height != Height)
            {
                Bounds = keepBottom && Top > area.Top + S(Edge)
                    ? new Rectangle(Left, bottom - height, Width, height)
                    : new Rectangle(Left, Top, Width, height);
            }
            LayoutCards();
            Invalidate();
        }

        protected override void OnDeactivate(EventArgs e)
        {
            base.OnDeactivate(e);
            HidePopup();
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.KeyCode == Keys.Escape) HidePopup();
        }

        public void HidePopup()
        {
            if (!Visible) return;
            LastHidden = Environment.TickCount;
            Hide();
        }

        protected override void OnDpiChanged(DpiChangedEventArgs e)
        {
            SetScale(e.DeviceDpiNew / 96f);
            base.OnDpiChanged(e);
            Relayout(keepBottom: true);
        }

        // ---- layout -------------------------------------------------------

        private int S(float value) => (int)Math.Round(value * scale);

        private void SetScale(float newScale)
        {
            if (titleFont != null && Math.Abs(newScale - scale) < 0.01f) return;
            scale = newScale;
            foreach (var font in new[] { titleFont, cardTitleFont, bodyFont, smallFont, smallBoldFont }) font?.Dispose();
            titleFont = new Font("Segoe UI Semibold", 14f * scale, GraphicsUnit.Pixel);
            cardTitleFont = new Font("Segoe UI Semibold", 13f * scale, GraphicsUnit.Pixel);
            bodyFont = new Font("Segoe UI", 12.5f * scale, GraphicsUnit.Pixel);
            smallFont = new Font("Segoe UI", 11.5f * scale, GraphicsUnit.Pixel);
            smallBoldFont = new Font("Segoe UI Semibold", 11.5f * scale, GraphicsUnit.Pixel);
        }

        private int CardHeight(RhinoInstance instance)
        {
            int lines = TitleLine + 2 + TextLine + (instance.Grasshopper != null ? TextLine : 0);
            int sessions = instance.Clients.Count == 0 ? TextLine : instance.Clients.Count * SessionHeight - 4;
            if (instance.Clients.Count > 1) sessions += TextLine + 2;
            return S(CardPadding) * 2 + S(lines) + S(DividerGap) * 2 + 1 + S(sessions);
        }

        private int MeasureHeight()
        {
            int body = instances.Count == 0
                ? S(96)
                : instances.Sum(CardHeight) + S(CardGap) * (instances.Count - 1);
            return S(HeaderHeight) + body + S(FooterHeight) + S(4);
        }

        private Rectangle CardViewport => new Rectangle(0, S(HeaderHeight),
            ClientSize.Width - (hasOverflow ? scrollBar.Width : 0),
            Math.Max(0, ClientSize.Height - S(HeaderHeight + FooterHeight)));

        private void LayoutCards()
        {
            int viewportHeight = Math.Max(1, ClientSize.Height - S(HeaderHeight + FooterHeight));
            int contentHeight = MeasureHeight() - S(HeaderHeight + FooterHeight);
            int maxScroll = Math.Max(0, contentHeight - viewportHeight);
            // Clamp before changing the range when instances disappear.
            if (scrollBar.Value > maxScroll) scrollBar.Value = maxScroll;
            hasOverflow = maxScroll > 0;
            scrollBar.Visible = hasOverflow;
            scrollBar.Bounds = new Rectangle(ClientSize.Width - scrollBar.Width, S(HeaderHeight),
                scrollBar.Width, viewportHeight);
            scrollBar.LargeChange = viewportHeight;
            scrollBar.SmallChange = S(SessionHeight);
            scrollBar.Maximum = Math.Max(0, contentHeight - 1);

            cards.Clear();
            int y = S(HeaderHeight) - scrollBar.Value;
            foreach (var instance in instances)
            {
                int h = CardHeight(instance);
                cards.Add((new Rectangle(S(Edge), y, CardViewport.Width - 2 * S(Edge), h), instance));
                y += h + S(CardGap);
            }
        }

        // ---- painting -----------------------------------------------------

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.Clear(theme.Background);
            g.SmoothingMode = SmoothingMode.AntiAlias;

            // Header: mark, title, summary.
            int markSize = S(18);
            var mark = new RectangleF(S(Edge + 2), (S(HeaderHeight) - markSize) / 2f, markSize, markSize);
            Theme.DrawMark(g, mark, instances.Any(i => i.Clients.Count > 0), theme.Background);
            var titleBox = new Rectangle((int)mark.Right + S(9), 0, S(160), S(HeaderHeight));
            DrawText(g, "RhinoMCP", titleFont, theme.Text, titleBox);

            int sessions = instances.Sum(i => i.Clients.Count);
            string summary = instances.Count == 0
                ? ""
                : $"{instances.Count} Rhino · {T.Sessions(sessions)}";
            DrawText(g, summary, smallFont, theme.Secondary,
                     new Rectangle(0, 0, ClientSize.Width - S(Edge + 4), S(HeaderHeight)), TextFormatFlags.Right);

            var cardClip = g.Save();
            g.SetClip(CardViewport);
            if (instances.Count == 0)
            {
                DrawEmpty(g);
            }
            else
            {
                for (int i = 0; i < cards.Count; i++) DrawCard(g, cards[i].Bounds, cards[i].Instance, i == hovered);
            }

            g.Restore(cardClip);

            // Footer hint.
            var footer = new Rectangle(S(Edge + 2), ClientSize.Height - S(FooterHeight), ClientSize.Width - 2 * S(Edge), S(FooterHeight));
            DrawText(g, instances.Count == 0 ? "" : T.ClickHint, smallFont, theme.Tertiary, footer);

            // 1 px outline, as on Windows 11 flyouts.
            using (var pen = new Pen(theme.CardBorder))
                g.DrawRectangle(pen, 0, 0, ClientSize.Width - 1, ClientSize.Height - 1);
        }

        private void DrawEmpty(Graphics g)
        {
            var box = new Rectangle(S(Edge), S(HeaderHeight), ClientSize.Width - 2 * S(Edge), S(96));
            FillCard(g, box, theme.Card);
            DrawText(g, T.EmptyTitle, cardTitleFont, theme.Text,
                     new Rectangle(box.Left, box.Top + S(24), box.Width, S(TitleLine)), TextFormatFlags.HorizontalCenter);
            DrawText(g, T.EmptyHint, smallFont, theme.Secondary,
                     new Rectangle(box.Left, box.Top + S(50), box.Width, S(TextLine)), TextFormatFlags.HorizontalCenter);
        }

        private void DrawCard(Graphics g, Rectangle box, RhinoInstance instance, bool hover)
        {
            FillCard(g, box, hover ? theme.CardHover : theme.Card);

            int pad = S(CardPadding);
            int left = box.Left + pad, right = box.Right - pad, width = right - left;
            int y = box.Top + pad;
            bool connected = instance.Clients.Count > 0;

            // Title row: status dot, port, Claude entry pill.
            int dot = S(8);
            using (var brush = new SolidBrush(connected ? theme.Connected : theme.Listening))
                g.FillEllipse(brush, left, y + (S(TitleLine) - dot) / 2f, dot, dot);

            string pill = instance.McpEntries.Count > 0 ? string.Join(", ", instance.McpEntries) : T.NoEntry;
            Size pillText = TextRenderer.MeasureText(g, pill, smallBoldFont, Size.Empty, TextFormatFlags.NoPadding);
            var pillBox = new Rectangle(right - pillText.Width - S(16), y + S(1), pillText.Width + S(16), S(TitleLine) - S(2));
            using (var path = Theme.RoundRect(pillBox, pillBox.Height / 2f))
            using (var brush = new SolidBrush(instance.McpEntries.Count > 0 ? theme.PillBack : Color.Transparent))
            using (var pen = new Pen(instance.McpEntries.Count > 0 ? theme.PillBack : theme.Warning))
            {
                g.FillPath(brush, path);
                g.DrawPath(pen, path);
            }
            DrawText(g, pill, smallBoldFont, instance.McpEntries.Count > 0 ? theme.PillText : theme.Warning,
                     pillBox, TextFormatFlags.HorizontalCenter);

            var titleBox = new Rectangle(left + dot + S(9), y, pillBox.Left - left - dot - S(17), S(TitleLine));
            string title = string.Format(T.Port, instance.Port);
            DrawText(g, title, cardTitleFont, theme.Text, titleBox);
            int titleWidth = TextRenderer.MeasureText(g, title, cardTitleFont, Size.Empty, TextFormatFlags.NoPadding).Width;
            DrawText(g, "·  " + string.Format(T.Since, instance.StartedAt.ToString("HH:mm")), smallFont, theme.Tertiary,
                     new Rectangle(titleBox.Left + titleWidth + S(6), y + S(1), titleBox.Width - titleWidth - S(6), S(TitleLine)));
            y += S(TitleLine) + S(2);

            // Documents.
            DrawLabelValue(g, "Rhino", instance.Document ?? T.Untitled, left, y, width);
            y += S(TextLine);
            if (instance.Grasshopper != null)
            {
                DrawLabelValue(g, "GH", instance.Grasshopper.Length > 0 ? instance.Grasshopper : T.NoDefinition,
                               left, y, width, dim: instance.Grasshopper.Length == 0);
                y += S(TextLine);
            }

            // Divider, then sessions.
            y += S(DividerGap);
            using (var pen = new Pen(theme.Divider)) g.DrawLine(pen, left, y, right, y);
            y += 1 + S(DividerGap);

            if (!connected)
            {
                DrawText(g, T.NoSession, smallFont, theme.Tertiary, new Rectangle(left, y, width, S(TextLine)));
                return;
            }
            foreach (var client in instance.Clients)
            {
                DrawSession(g, client, left, y, width);
                y += S(SessionHeight);
            }
            if (instance.Clients.Count > 1)
            {
                // Legal, but usually a mistake: two Claude sessions editing one model.
                DrawText(g, "\u26A0  " + string.Format(T.SharedRhino, instance.Clients.Count), smallFont, theme.Warning,
                         new Rectangle(left, y - S(2), width, S(TextLine)));
            }
        }

        private void DrawLabelValue(Graphics g, string label, string value, int left, int y, int width, bool dim = false)
        {
            int labelWidth = S(50);
            DrawText(g, label, smallFont, theme.Secondary, new Rectangle(left, y, labelWidth, S(TextLine)));
            DrawText(g, value, bodyFont, dim ? theme.Tertiary : theme.Text, new Rectangle(left + labelWidth, y, width - labelWidth, S(TextLine)));
        }

        private void DrawSession(Graphics g, ClientInfo client, int left, int y, int width)
        {
            // Round avatar with the client's initial, tinted with the "connected" colour.
            int avatar = S(24);
            var circle = new RectangleF(left, y + (S(SessionHeight) - S(4) - avatar) / 2f, avatar, avatar);
            using (var brush = new SolidBrush(Color.FromArgb(38, theme.Connected))) g.FillEllipse(brush, circle);
            string initial = string.IsNullOrEmpty(client.App) ? "?" : client.App.Substring(0, 1).ToUpperInvariant();
            DrawText(g, initial, smallBoldFont, theme.Connected, Rectangle.Round(circle), TextFormatFlags.HorizontalCenter);

            int textLeft = left + avatar + S(10), textWidth = width - avatar - S(10);
            DateTime lastSeen = client.LastCommandAt ?? client.ConnectedAt;
            string ago = Ago(lastSeen);
            int agoWidth = TextRenderer.MeasureText(g, ago, smallFont, Size.Empty, TextFormatFlags.NoPadding).Width;
            DrawText(g, ago, smallFont, theme.Tertiary, new Rectangle(textLeft, y, textWidth, S(TextLine)), TextFormatFlags.Right);

            // Project folder first: it is what tells two Claude sessions apart.
            DrawText(g, client.Folder ?? client.App, bodyFont, theme.Text,
                     new Rectangle(textLeft, y, textWidth - agoWidth - S(10), S(TextLine)));

            // The avatar already says "C"; name the app only when it is not Claude Code.
            string detail = client.Folder == null || client.App == "Claude Code" ? "" : client.App + "  ·  ";
            detail += client.Commands == 0
                ? T.NoCommands
                : $"{T.Commands(client.Commands)}  ·  {client.LastCommand}";
            DrawText(g, detail, smallFont, theme.Secondary, new Rectangle(textLeft, y + S(TextLine) - S(2), textWidth, S(TextLine)));
        }

        private void FillCard(Graphics g, Rectangle box, Color fill)
        {
            using (var path = Theme.RoundRect(new RectangleF(box.Left + 0.5f, box.Top + 0.5f, box.Width - 1, box.Height - 1), S(CardRadius)))
            using (var brush = new SolidBrush(fill))
            using (var pen = new Pen(theme.CardBorder))
            {
                g.FillPath(brush, path);
                g.DrawPath(pen, path);
            }
        }

        private static void DrawText(Graphics g, string text, Font font, Color color, Rectangle box,
                                     TextFormatFlags extra = TextFormatFlags.Left)
        {
            TextRenderer.DrawText(g, text, font, box, color,
                extra | TextFormatFlags.VerticalCenter | TextFormatFlags.SingleLine |
                TextFormatFlags.EndEllipsis | TextFormatFlags.NoPrefix | TextFormatFlags.NoPadding);
        }

        private static string Ago(DateTime when)
        {
            var span = DateTime.Now - when;
            if (span.TotalSeconds < 10) return T.JustNow;
            if (span.TotalMinutes < 1) return string.Format(T.SecondsAgo, (int)span.TotalSeconds);
            if (span.TotalHours < 1) return string.Format(T.MinutesAgo, (int)span.TotalMinutes);
            if (span.TotalDays < 1) return string.Format(T.HoursAgo, (int)span.TotalHours);
            return when.ToString("dd MMM HH:mm");
        }

        // ---- interaction --------------------------------------------------

        protected override void OnMouseWheel(MouseEventArgs e)
        {
            base.OnMouseWheel(e);
            if (!scrollBar.Visible) return;
            int lines = SystemInformation.MouseWheelScrollLines;
            int step = lines < 0 ? scrollBar.LargeChange : lines * scrollBar.SmallChange;
            int maximum = scrollBar.Maximum - scrollBar.LargeChange + 1;
            scrollBar.Value = Math.Max(0, Math.Min(maximum,
                scrollBar.Value - e.Delta * step / SystemInformation.MouseWheelScrollDelta));
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            int index = CardViewport.Contains(e.Location)
                ? cards.FindIndex(c => c.Bounds.Contains(e.Location)) : -1;
            if (index == hovered) return;
            hovered = index;
            Cursor = index >= 0 ? Cursors.Hand : Cursors.Default;
            Invalidate();
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            base.OnMouseLeave(e);
            if (hovered < 0) return;
            hovered = -1;
            Invalidate();
        }

        protected override void OnMouseClick(MouseEventArgs e)
        {
            base.OnMouseClick(e);
            int index = CardViewport.Contains(e.Location)
                ? cards.FindIndex(c => c.Bounds.Contains(e.Location)) : -1;
            if (index < 0 || e.Button != MouseButtons.Left) return;
            ActivateRhino(cards[index].Instance.Pid);
            HidePopup();
        }

        private static void ActivateRhino(int pid)
        {
            try
            {
                using (var process = Process.GetProcessById(pid))
                {
                    IntPtr window = process.MainWindowHandle;
                    if (window == IntPtr.Zero) return;
                    if (IsIconic(window)) ShowWindow(window, 9); // SW_RESTORE
                    SetForegroundWindow(window);
                }
            }
            catch (Exception)
            {
                // Rhino closed meanwhile.
            }
        }

        private static float MonitorDpi(Screen screen)
        {
            try
            {
                var center = new Point(screen.Bounds.Left + screen.Bounds.Width / 2, screen.Bounds.Top + screen.Bounds.Height / 2);
                IntPtr monitor = MonitorFromPoint(center, 2); // MONITOR_DEFAULTTONEAREST
                return GetDpiForMonitor(monitor, 0, out uint dpi, out _) == 0 ? dpi : 96f;
            }
            catch (Exception)
            {
                return 96f;
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                foreach (var font in new[] { titleFont, cardTitleFont, bodyFont, smallFont, smallBoldFont }) font?.Dispose();
            }
            base.Dispose(disposing);
        }

        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attribute, ref int value, int size);

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hwnd, int command);

        [DllImport("user32.dll")]
        private static extern bool IsIconic(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern IntPtr MonitorFromPoint(Point point, uint flags);

        [DllImport("shcore.dll")]
        private static extern int GetDpiForMonitor(IntPtr monitor, int dpiType, out uint dpiX, out uint dpiY);
    }
}
