using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using Grasshopper;
using Grasshopper.GUI;
using Grasshopper.GUI.Canvas;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Attributes;

namespace GrasshopperMCPPlugin.Components;

/// <summary>
/// Grasshopper component to control the MCP server.
/// This is a self-contained component with no inputs/outputs.
/// Place this component on the canvas to start the server automatically.
/// </summary>
public class MCPServerComponent : GH_Component
{
    private const int DEFAULT_PORT = 2000;
    private bool _autoStarted = false;

    public MCPServerComponent()
        : base(
            "MCP Server",
            "MCP",
            "GrasshopperMCP Server - enables AI agent communication.\nPlace on canvas to start automatically.",
            "Params",
            "Util")
    {
        // Subscribe to log updates to refresh display
        MCPLogger.OnLogAdded += OnLogUpdated;
    }

    ~MCPServerComponent()
    {
        MCPLogger.OnLogAdded -= OnLogUpdated;
    }

    private void OnLogUpdated()
    {
        // Schedule a solution expiration to update the display
        Rhino.RhinoApp.InvokeOnUiThread((Action)(() =>
        {
            ExpireSolution(true);
        }));
    }

    public override Guid ComponentGuid => new Guid("F1E2D3C4-B5A6-7890-1234-567890ABCDEF");

    protected override Bitmap? Icon => null;

    public override void CreateAttributes()
    {
        m_attributes = new MCPServerAttributes(this);
    }

    protected override void RegisterInputParams(GH_InputParamManager pManager)
    {
        // No inputs - self-contained component
    }

    protected override void RegisterOutputParams(GH_OutputParamManager pManager)
    {
        // No outputs - self-contained component
    }

    public override void AddedToDocument(GH_Document document)
    {
        base.AddedToDocument(document);

        // Auto-start the server when component is added to canvas
        if (!_autoStarted && !GrasshopperMCPServerController.IsRunning())
        {
            try
            {
                GrasshopperMCPServerController.Start("127.0.0.1", DEFAULT_PORT);
                _autoStarted = true;
                MCPLogger.Log("MCP Server started automatically");
            }
            catch (Exception ex)
            {
                MCPLogger.Log($"Failed to auto-start: {ex.Message}");
            }
        }
    }

    public override void RemovedFromDocument(GH_Document document)
    {
        // Stop server when component is removed
        if (GrasshopperMCPServerController.IsRunning())
        {
            GrasshopperMCPServerController.Stop();
            MCPLogger.Log("MCP Server stopped (component removed)");
        }

        base.RemovedFromDocument(document);
    }

    protected override void SolveInstance(IGH_DataAccess DA)
    {
        // No-op - server runs independently
    }

    public bool IsServerRunning => GrasshopperMCPServerController.IsRunning();

    public void StartServer()
    {
        if (!GrasshopperMCPServerController.IsRunning())
        {
            try
            {
                GrasshopperMCPServerController.Start("127.0.0.1", DEFAULT_PORT);
                _autoStarted = true;
                MCPLogger.Log("MCP Server started");
            }
            catch (Exception ex)
            {
                MCPLogger.Log($"Failed to start: {ex.Message}");
            }
        }
    }

    public void StopServer()
    {
        if (GrasshopperMCPServerController.IsRunning())
        {
            GrasshopperMCPServerController.Stop();
            MCPLogger.Log("MCP Server stopped");
        }
    }

    public List<string> GetLogs() => MCPLogger.GetLogs();
}

/// <summary>
/// Custom resizable attributes for the MCP Server component.
/// Uses calendar-like color scheme with scrollable logs area.
/// </summary>
public class MCPServerAttributes : GH_ComponentAttributes
{
    // Size constraints
    private const int MIN_WIDTH = 220;
    private const int MAX_WIDTH = 500;
    private const int MIN_HEIGHT = 140;
    private const int MAX_HEIGHT = 400;

    // Layout constants
    private const int HEADER_HEIGHT = 28;
    private const int STATUS_HEIGHT = 24;
    private const int BUTTON_HEIGHT = 26;
    private const int PADDING = 8;
    private const int RESIZE_GRIP_SIZE = 12;
    private const int SCROLLBAR_WIDTH = 12;
    private const float LINE_HEIGHT = 15f;

    // Colors - Calendar-like scheme
    private static readonly Color BgColor = Color.FromArgb(245, 245, 245);
    private static readonly Color HeaderBgColor = Color.FromArgb(70, 70, 70);
    private static readonly Color BorderColor = Color.FromArgb(180, 180, 180);
    private static readonly Color LogsBgColor = Color.FromArgb(255, 255, 255);
    private static readonly Color LogsTextColor = Color.FromArgb(60, 60, 60);
    private static readonly Color ScrollbarBgColor = Color.FromArgb(230, 230, 230);
    private static readonly Color ScrollbarThumbColor = Color.FromArgb(180, 180, 180);
    private static readonly Color ScrollbarThumbHoverColor = Color.FromArgb(160, 160, 160);
    private static readonly Color StatusRunningColor = Color.FromArgb(46, 139, 87);
    private static readonly Color StatusStoppedColor = Color.FromArgb(180, 80, 50);

    // Button colors
    private static readonly Color ButtonBgColor = Color.FromArgb(240, 240, 240);
    private static readonly Color ButtonBorderColor = Color.FromArgb(160, 160, 160);
    private static readonly Color ButtonPressedColor = Color.FromArgb(200, 200, 200);
    private static readonly Color ButtonTextColor = Color.FromArgb(40, 40, 40);

    // Bounds
    private RectangleF _buttonBounds;
    private RectangleF _resizeGripBounds;
    private RectangleF _logsBounds;
    private RectangleF _scrollbarBounds;
    private RectangleF _scrollbarThumbBounds;

    // Interaction state
    private bool _isResizing = false;
    private PointF _resizeStartPoint;
    private SizeF _resizeStartSize;
    private bool _buttonPressed = false;
    private bool _scrollbarDragging = false;
    private float _scrollbarDragStartY;
    private float _scrollOffsetStart;

    // Scroll state
    private float _scrollOffset = 0;
    private int _totalLogLines = 0;
    private int _visibleLines = 0;

    // Custom size
    private float _customWidth = MIN_WIDTH;
    private float _customHeight = 180;

    public MCPServerAttributes(MCPServerComponent owner) : base(owner)
    {
    }

    public new MCPServerComponent Owner => (MCPServerComponent)base.Owner;

    protected override void Layout()
    {
        // Clamp to min/max
        _customWidth = Math.Max(MIN_WIDTH, Math.Min(MAX_WIDTH, _customWidth));
        _customHeight = Math.Max(MIN_HEIGHT, Math.Min(MAX_HEIGHT, _customHeight));

        // Set bounds with custom size
        Bounds = new RectangleF(Pivot.X, Pivot.Y, _customWidth, _customHeight);

        // Button at bottom
        _buttonBounds = new RectangleF(
            Bounds.X + PADDING,
            Bounds.Bottom - BUTTON_HEIGHT - PADDING,
            Bounds.Width - PADDING * 2,
            BUTTON_HEIGHT);

        // Resize grip in bottom-right corner
        _resizeGripBounds = new RectangleF(
            Bounds.Right - RESIZE_GRIP_SIZE,
            Bounds.Bottom - RESIZE_GRIP_SIZE,
            RESIZE_GRIP_SIZE,
            RESIZE_GRIP_SIZE);

        // Logs area (between status and button)
        float logsTop = Bounds.Y + HEADER_HEIGHT + STATUS_HEIGHT + 4;
        float logsBottom = _buttonBounds.Y - 6;
        float logsHeight = logsBottom - logsTop;
        _logsBounds = new RectangleF(Bounds.X + PADDING, logsTop, Bounds.Width - PADDING * 2, logsHeight);

        // Calculate visible lines
        _visibleLines = Math.Max(1, (int)((logsHeight - 6) / LINE_HEIGHT));

        // Scrollbar bounds (inside logs area, on right side)
        _scrollbarBounds = new RectangleF(
            _logsBounds.Right - SCROLLBAR_WIDTH - 2,
            _logsBounds.Y + 2,
            SCROLLBAR_WIDTH,
            _logsBounds.Height - 4);

        UpdateScrollbarThumb();
    }

    private void UpdateScrollbarThumb()
    {
        var logs = Owner.GetLogs();
        _totalLogLines = logs.Count;

        if (_totalLogLines <= _visibleLines)
        {
            // No scrolling needed - thumb fills entire scrollbar
            _scrollbarThumbBounds = _scrollbarBounds;
            _scrollOffset = 0;
        }
        else
        {
            // Calculate thumb size and position
            float thumbRatio = (float)_visibleLines / _totalLogLines;
            float thumbHeight = Math.Max(20, _scrollbarBounds.Height * thumbRatio);

            float scrollableRange = _totalLogLines - _visibleLines;
            float scrollRatio = _scrollOffset / scrollableRange;
            float thumbY = _scrollbarBounds.Y + scrollRatio * (_scrollbarBounds.Height - thumbHeight);

            _scrollbarThumbBounds = new RectangleF(
                _scrollbarBounds.X,
                thumbY,
                _scrollbarBounds.Width,
                thumbHeight);
        }
    }

    protected override void Render(GH_Canvas canvas, Graphics graphics, GH_CanvasChannel channel)
    {
        if (channel != GH_CanvasChannel.Objects) return;

        graphics.SmoothingMode = SmoothingMode.HighQuality;
        graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

        bool isRunning = Owner.IsServerRunning;

        // Main background - light grey like calendar
        using (var bgBrush = new SolidBrush(BgColor))
        {
            var bgPath = CreateRoundedRect(Bounds, 4);
            graphics.FillPath(bgBrush, bgPath);
            bgPath.Dispose();
        }

        // Border - subtle like calendar
        using (var borderPen = new Pen(Selected ? Color.FromArgb(100, 150, 200) : BorderColor, Selected ? 2f : 1f))
        {
            var borderPath = CreateRoundedRect(Bounds, 4);
            graphics.DrawPath(borderPen, borderPath);
            borderPath.Dispose();
        }

        // Header bar - dark like calendar footer
        var headerBounds = new RectangleF(Bounds.X + 1, Bounds.Y + 1, Bounds.Width - 2, HEADER_HEIGHT);
        using (var headerBrush = new SolidBrush(HeaderBgColor))
        {
            var headerPath = CreateRoundedRect(headerBounds, 3, true, true, false, false);
            graphics.FillPath(headerBrush, headerPath);
            headerPath.Dispose();
        }

        // Header text
        using (var headerFormat = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
        {
            graphics.DrawString("MCP Server", GH_FontServer.StandardBold, Brushes.White, headerBounds, headerFormat);
        }

        // Status area with indicator dot
        float statusY = Bounds.Y + HEADER_HEIGHT + 4;
        var statusBounds = new RectangleF(Bounds.X + PADDING, statusY, Bounds.Width - PADDING * 2, STATUS_HEIGHT);

        // Status indicator dot
        float dotSize = 10;
        float dotX = statusBounds.X + 8;
        float dotY = statusBounds.Y + (STATUS_HEIGHT - dotSize) / 2;
        Color statusColor = isRunning ? StatusRunningColor : StatusStoppedColor;

        using (var dotBrush = new SolidBrush(statusColor))
        {
            graphics.FillEllipse(dotBrush, dotX, dotY, dotSize, dotSize);
        }

        // Status text
        string statusText = isRunning ? "Running" : "Stopped";
        var statusTextBounds = new RectangleF(dotX + dotSize + 6, statusBounds.Y, statusBounds.Width - dotSize - 20, STATUS_HEIGHT);
        using (var statusBrush = new SolidBrush(Color.FromArgb(60, 60, 60)))
        using (var statusFormat = new StringFormat { Alignment = StringAlignment.Near, LineAlignment = StringAlignment.Center })
        {
            graphics.DrawString(statusText, GH_FontServer.Standard, statusBrush, statusTextBounds, statusFormat);
        }

        // Logs area
        if (_logsBounds.Height > 20)
        {
            // Logs background - white
            using (var logsBgBrush = new SolidBrush(LogsBgColor))
            {
                var logsPath = CreateRoundedRect(_logsBounds, 3);
                graphics.FillPath(logsBgBrush, logsPath);
                logsPath.Dispose();
            }

            // Logs border
            using (var logsBorderPen = new Pen(BorderColor, 1))
            {
                var logsPath = CreateRoundedRect(_logsBounds, 3);
                graphics.DrawPath(logsBorderPen, logsPath);
                logsPath.Dispose();
            }

            // Draw logs with clipping
            var logs = Owner.GetLogs();
            _totalLogLines = logs.Count;
            UpdateScrollbarThumb();

            // Set clip region for logs text
            var oldClip = graphics.Clip;
            var logsTextBounds = new RectangleF(
                _logsBounds.X + 4,
                _logsBounds.Y + 3,
                _logsBounds.Width - SCROLLBAR_WIDTH - 10,
                _logsBounds.Height - 6);
            graphics.SetClip(logsTextBounds);

            using (var logFont = new Font("Consolas", 8.5f))
            using (var logBrush = new SolidBrush(LogsTextColor))
            using (var dimBrush = new SolidBrush(Color.FromArgb(150, 150, 150)))
            using (var logFormat = new StringFormat { Trimming = StringTrimming.EllipsisCharacter })
            {
                if (logs.Count == 0)
                {
                    graphics.Clip = oldClip;
                    logFormat.Alignment = StringAlignment.Center;
                    logFormat.LineAlignment = StringAlignment.Center;
                    var emptyBounds = new RectangleF(_logsBounds.X, _logsBounds.Y, _logsBounds.Width - SCROLLBAR_WIDTH, _logsBounds.Height);
                    graphics.DrawString("No logs yet", logFont, dimBrush, emptyBounds, logFormat);
                }
                else
                {
                    int startIndex = (int)_scrollOffset;
                    startIndex = Math.Max(0, Math.Min(startIndex, logs.Count - _visibleLines));

                    float y = logsTextBounds.Y;
                    for (int i = startIndex; i < logs.Count && i < startIndex + _visibleLines + 1; i++)
                    {
                        var lineRect = new RectangleF(logsTextBounds.X, y, logsTextBounds.Width, LINE_HEIGHT);
                        graphics.DrawString(logs[i], logFont, logBrush, lineRect, logFormat);
                        y += LINE_HEIGHT;
                    }
                    graphics.Clip = oldClip;
                }
            }

            // Draw scrollbar if needed
            if (_totalLogLines > _visibleLines)
            {
                // Scrollbar track
                using (var trackBrush = new SolidBrush(ScrollbarBgColor))
                {
                    var trackPath = CreateRoundedRect(_scrollbarBounds, 4);
                    graphics.FillPath(trackBrush, trackPath);
                    trackPath.Dispose();
                }

                // Scrollbar thumb
                Color thumbColor = _scrollbarDragging ? ScrollbarThumbHoverColor : ScrollbarThumbColor;
                using (var thumbBrush = new SolidBrush(thumbColor))
                {
                    var thumbPath = CreateRoundedRect(_scrollbarThumbBounds, 4);
                    graphics.FillPath(thumbBrush, thumbPath);
                    thumbPath.Dispose();
                }
            }
        }

        // Button - Grasshopper style with 3D effect
        DrawButton(graphics, _buttonBounds, isRunning ? "Stop Server" : "Start Server", _buttonPressed);

        // Resize grip indicator
        using (var gripPen = new Pen(Color.FromArgb(160, 160, 160), 1))
        {
            float gx = Bounds.Right - 4;
            float gy = Bounds.Bottom - 4;
            graphics.DrawLine(gripPen, gx - 8, gy, gx, gy - 8);
            graphics.DrawLine(gripPen, gx - 5, gy, gx, gy - 5);
            graphics.DrawLine(gripPen, gx - 2, gy, gx, gy - 2);
        }
    }

    private void DrawButton(Graphics graphics, RectangleF bounds, string text, bool pressed)
    {
        // Button background with gradient for 3D effect
        Color topColor, bottomColor;
        if (pressed)
        {
            topColor = Color.FromArgb(200, 200, 200);
            bottomColor = Color.FromArgb(220, 220, 220);
        }
        else
        {
            topColor = Color.FromArgb(250, 250, 250);
            bottomColor = Color.FromArgb(230, 230, 230);
        }

        using (var gradientBrush = new LinearGradientBrush(bounds, topColor, bottomColor, LinearGradientMode.Vertical))
        {
            var buttonPath = CreateRoundedRect(bounds, 3);
            graphics.FillPath(gradientBrush, buttonPath);
            buttonPath.Dispose();
        }

        // Button border
        using (var borderPen = new Pen(ButtonBorderColor, 1))
        {
            var buttonPath = CreateRoundedRect(bounds, 3);
            graphics.DrawPath(borderPen, buttonPath);
            buttonPath.Dispose();
        }

        // Inner highlight (top edge) when not pressed
        if (!pressed)
        {
            using (var highlightPen = new Pen(Color.FromArgb(100, 255, 255, 255), 1))
            {
                graphics.DrawLine(highlightPen, bounds.X + 4, bounds.Y + 1, bounds.Right - 4, bounds.Y + 1);
            }
        }

        // Button text
        var textBounds = pressed ? new RectangleF(bounds.X, bounds.Y + 1, bounds.Width, bounds.Height) : bounds;
        using (var textFormat = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
        using (var textBrush = new SolidBrush(ButtonTextColor))
        {
            graphics.DrawString(text, GH_FontServer.Standard, textBrush, textBounds, textFormat);
        }
    }

    private GraphicsPath CreateRoundedRect(RectangleF rect, float radius, bool tl = true, bool tr = true, bool br = true, bool bl = true)
    {
        var path = new GraphicsPath();
        float d = radius * 2;

        if (tl)
            path.AddArc(rect.X, rect.Y, d, d, 180, 90);
        else
            path.AddLine(rect.X, rect.Y, rect.X + radius, rect.Y);

        path.AddLine(rect.X + (tl ? radius : 0), rect.Y, rect.Right - (tr ? radius : 0), rect.Y);

        if (tr)
            path.AddArc(rect.Right - d, rect.Y, d, d, 270, 90);
        else
            path.AddLine(rect.Right, rect.Y, rect.Right, rect.Y + radius);

        path.AddLine(rect.Right, rect.Y + (tr ? radius : 0), rect.Right, rect.Bottom - (br ? radius : 0));

        if (br)
            path.AddArc(rect.Right - d, rect.Bottom - d, d, d, 0, 90);
        else
            path.AddLine(rect.Right, rect.Bottom, rect.Right - radius, rect.Bottom);

        path.AddLine(rect.Right - (br ? radius : 0), rect.Bottom, rect.X + (bl ? radius : 0), rect.Bottom);

        if (bl)
            path.AddArc(rect.X, rect.Bottom - d, d, d, 90, 90);
        else
            path.AddLine(rect.X, rect.Bottom, rect.X, rect.Bottom - radius);

        path.AddLine(rect.X, rect.Bottom - (bl ? radius : 0), rect.X, rect.Y + (tl ? radius : 0));

        path.CloseFigure();
        return path;
    }

    public override GH_ObjectResponse RespondToMouseDown(GH_Canvas sender, GH_CanvasMouseEvent e)
    {
        // Check if click is on scrollbar thumb
        if (_scrollbarThumbBounds.Contains(e.CanvasLocation) && _totalLogLines > _visibleLines)
        {
            _scrollbarDragging = true;
            _scrollbarDragStartY = e.CanvasLocation.Y;
            _scrollOffsetStart = _scrollOffset;
            return GH_ObjectResponse.Capture;
        }

        // Check if click is on scrollbar track (page up/down)
        if (_scrollbarBounds.Contains(e.CanvasLocation) && _totalLogLines > _visibleLines)
        {
            if (e.CanvasLocation.Y < _scrollbarThumbBounds.Y)
            {
                // Page up
                _scrollOffset = Math.Max(0, _scrollOffset - _visibleLines);
            }
            else if (e.CanvasLocation.Y > _scrollbarThumbBounds.Bottom)
            {
                // Page down
                _scrollOffset = Math.Min(_totalLogLines - _visibleLines, _scrollOffset + _visibleLines);
            }
            Owner.ExpireSolution(true);
            return GH_ObjectResponse.Handled;
        }

        // Check if click is on resize grip
        if (_resizeGripBounds.Contains(e.CanvasLocation))
        {
            _isResizing = true;
            _resizeStartPoint = e.CanvasLocation;
            _resizeStartSize = new SizeF(_customWidth, _customHeight);
            return GH_ObjectResponse.Capture;
        }

        // Check if click is on button
        if (_buttonBounds.Contains(e.CanvasLocation))
        {
            _buttonPressed = true;
            Owner.ExpireSolution(true);
            return GH_ObjectResponse.Capture;
        }

        return base.RespondToMouseDown(sender, e);
    }

    public override GH_ObjectResponse RespondToMouseMove(GH_Canvas sender, GH_CanvasMouseEvent e)
    {
        if (_scrollbarDragging)
        {
            float dy = e.CanvasLocation.Y - _scrollbarDragStartY;
            float scrollableHeight = _scrollbarBounds.Height - _scrollbarThumbBounds.Height;
            float scrollableRange = _totalLogLines - _visibleLines;

            if (scrollableHeight > 0)
            {
                float deltaScroll = (dy / scrollableHeight) * scrollableRange;
                _scrollOffset = Math.Max(0, Math.Min(scrollableRange, _scrollOffsetStart + deltaScroll));
            }

            Owner.ExpireSolution(true);
            return GH_ObjectResponse.Handled;
        }

        if (_isResizing)
        {
            float dx = e.CanvasLocation.X - _resizeStartPoint.X;
            float dy = e.CanvasLocation.Y - _resizeStartPoint.Y;

            _customWidth = _resizeStartSize.Width + dx;
            _customHeight = _resizeStartSize.Height + dy;

            _customWidth = Math.Max(MIN_WIDTH, Math.Min(MAX_WIDTH, _customWidth));
            _customHeight = Math.Max(MIN_HEIGHT, Math.Min(MAX_HEIGHT, _customHeight));

            ExpireLayout();
            Owner.ExpireSolution(true);

            return GH_ObjectResponse.Handled;
        }

        // Update button pressed state if dragging outside
        if (_buttonPressed && !_buttonBounds.Contains(e.CanvasLocation))
        {
            _buttonPressed = false;
            Owner.ExpireSolution(true);
        }

        return base.RespondToMouseMove(sender, e);
    }

    public override GH_ObjectResponse RespondToMouseUp(GH_Canvas sender, GH_CanvasMouseEvent e)
    {
        if (_scrollbarDragging)
        {
            _scrollbarDragging = false;
            Owner.ExpireSolution(true);
            return GH_ObjectResponse.Release;
        }

        if (_isResizing)
        {
            _isResizing = false;
            return GH_ObjectResponse.Release;
        }

        if (_buttonPressed)
        {
            _buttonPressed = false;

            // Only trigger action if mouse is still over button
            if (_buttonBounds.Contains(e.CanvasLocation))
            {
                if (Owner.IsServerRunning)
                {
                    Owner.StopServer();
                }
                else
                {
                    Owner.StartServer();
                }
            }

            Owner.ExpireSolution(true);
            return GH_ObjectResponse.Release;
        }

        return base.RespondToMouseUp(sender, e);
    }

    public override GH_ObjectResponse RespondToMouseDoubleClick(GH_Canvas sender, GH_CanvasMouseEvent e)
    {
        // Don't handle double-click on interactive areas
        if (_buttonBounds.Contains(e.CanvasLocation) ||
            _scrollbarBounds.Contains(e.CanvasLocation) ||
            _logsBounds.Contains(e.CanvasLocation))
        {
            return GH_ObjectResponse.Handled;
        }

        return base.RespondToMouseDoubleClick(sender, e);
    }
}
