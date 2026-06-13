using System;
using System.Diagnostics.CodeAnalysis;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Display;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Captures a viewport screenshot and returns it as base64-encoded PNG data.
    /// </summary>
    /// <remarks>
    /// System.Drawing.Common encoding APIs are flagged Windows-only by the
    /// analyzer (CA1416), but RhinoCommon's CaptureToBitmap returns a
    /// System.Drawing.Bitmap on both Windows and Mac because Rhino ships its
    /// own GDI+/libgdiplus support. We accept the limitation that this tool
    /// only works hosted inside the Rhino process — a clear error is returned
    /// at runtime if encoding fails on a platform without that support.
    /// </remarks>
    [McpCommand("capture_viewport", ReadOnly = true)]
    [SuppressMessage("Interoperability", "CA1416:Validate platform compatibility",
        Justification = "Runs in the Rhino process which provides cross-platform System.Drawing support.")]
    public JObject CaptureViewport(JObject parameters)
    {
        RhinoApp.WriteLine("Capturing viewport...");
        var doc = RhinoDoc.ActiveDoc;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Rhino document. Please open or create a document.");
        }

        // Parse parameters with defaults
        string viewportTarget = parameters["viewport"]?.ToString()?.ToLower() ?? "active";
        int width = Math.Min(parameters["width"]?.ToObject<int>() ?? 800, 4096);
        int height = Math.Min(parameters["height"]?.ToObject<int>() ?? 600, 4096);
        bool showGrid = parameters["show_grid"]?.ToObject<bool>() ?? true;
        bool showAxes = parameters["show_axes"]?.ToObject<bool>() ?? true;
        bool showCplaneAxes = parameters["show_cplane_axes"]?.ToObject<bool>() ?? false;
        bool zoomToFit = parameters["zoom_to_fit"]?.ToObject<bool>() ?? false;

        // Ensure minimum dimensions
        width = Math.Max(width, 100);
        height = Math.Max(height, 100);

        // capture_viewport is ReadOnly, so it must leave every viewport exactly as it
        // found it. Resolving a projection target (top/front/...) reprojects AND renames
        // the active view, and zoom_to_fit moves the camera, so snapshot the projection
        // and name of the views we might touch and restore them in the finally below.
        RhinoView activeView = doc.Views.ActiveView;
        ViewportInfo savedActiveState = activeView != null
            ? new ViewportInfo(activeView.ActiveViewport)
            : null;
        string savedActiveName = activeView?.ActiveViewport.Name;

        // Find the target view (may temporarily reproject the active view)
        RhinoView targetView = GetTargetView(doc, viewportTarget);
        if (targetView == null)
        {
            throw new InvalidOperationException($"Viewport '{viewportTarget}' not found. Available viewports: Perspective, Top, Front, Right, Back, Left, Bottom, or use 'active' for the current view.");
        }

        // A named projection view (e.g. an existing "Top") is a different view than the
        // active one; snapshot it too since zoom_to_fit would otherwise leave it zoomed.
        bool targetIsActive = activeView != null
            && targetView.ActiveViewportID == activeView.ActiveViewportID;
        ViewportInfo savedTargetState = !targetIsActive
            ? new ViewportInfo(targetView.ActiveViewport)
            : null;
        string savedTargetName = !targetIsActive ? targetView.ActiveViewport.Name : null;

        try
        {
            // Store viewport name
            string viewportName = targetView.ActiveViewport.Name ?? viewportTarget;

            // Apply zoom to fit if requested
            if (zoomToFit && doc.Objects.Count > 0)
            {
                targetView.ActiveViewport.ZoomExtents();
                doc.Views.Redraw();
            }

            string base64Data = CaptureViewToPngBase64(
                targetView,
                width,
                height,
                showGrid,
                showAxes,
                showCplaneAxes,
                "capture_viewport");

            RhinoApp.WriteLine($"Captured viewport '{viewportName}' ({width}x{height})");

            return new JObject
            {
                ["image_data"] = base64Data,
                ["mime_type"] = "image/png",
                ["width"] = width,
                ["height"] = height,
                ["viewport_name"] = viewportName,
                ["viewport_target"] = viewportTarget,
                ["show_grid"] = showGrid,
                ["show_axes"] = showAxes,
                ["show_cplane_axes"] = showCplaneAxes,
                ["object_count"] = doc.Objects.Count
            };
        }
        finally
        {
            // Restore any viewport we may have changed (projection and name) so the
            // capture leaves no visible side effect on the user's views.
            if (savedActiveState != null)
            {
                activeView.ActiveViewport.SetViewProjection(savedActiveState, true);
                if (savedActiveName != null && activeView.ActiveViewport.Name != savedActiveName)
                    activeView.ActiveViewport.Name = savedActiveName;
            }
            if (savedTargetState != null)
            {
                targetView.ActiveViewport.SetViewProjection(savedTargetState, true);
                if (savedTargetName != null && targetView.ActiveViewport.Name != savedTargetName)
                    targetView.ActiveViewport.Name = savedTargetName;
            }
            doc.Views.Redraw();
        }
    }

    [SuppressMessage("Interoperability", "CA1416:Validate platform compatibility",
        Justification = "Runs in the Rhino process which provides cross-platform System.Drawing support.")]
    private static string CaptureViewToPngBase64(
        RhinoView targetView,
        int width,
        int height,
        bool showGrid,
        bool showAxes,
        bool showCplaneAxes,
        string commandName)
    {
        Size captureSize = new Size(width, height);
        Bitmap bitmap = targetView.CaptureToBitmap(captureSize, showGrid, showAxes, showCplaneAxes);
        if (bitmap == null)
        {
            throw new InvalidOperationException("Failed to capture viewport bitmap. The viewport may be minimized or hidden.");
        }

        try
        {
            using MemoryStream ms = new MemoryStream();
            bitmap.Save(ms, ImageFormat.Png);
            byte[] imageBytes = ms.ToArray();
            return Convert.ToBase64String(imageBytes);
        }
        catch (PlatformNotSupportedException ex)
        {
            throw new InvalidOperationException(
                $"{commandName}: PNG encoding is not supported on this platform. " +
                "On macOS/Linux this requires running inside Rhino with its bundled " +
                "libgdiplus.", ex);
        }
        finally
        {
            bitmap.Dispose();
        }
    }

    /// <summary>
    /// Gets the target RhinoView based on viewport identifier.
    /// </summary>
    private RhinoView GetTargetView(RhinoDoc doc, string viewportTarget)
    {
        switch (viewportTarget.ToLower())
        {
            case "active":
                return doc.Views.ActiveView;

            case "perspective":
                foreach (var view in doc.Views)
                {
                    if (view.ActiveViewport.IsPerspectiveProjection)
                        return view;
                }
                // Fall back to active if no perspective found
                return doc.Views.ActiveView;

            case "top":
                return FindViewByProjection(doc, DefinedViewportProjection.Top);

            case "front":
                return FindViewByProjection(doc, DefinedViewportProjection.Front);

            case "right":
                return FindViewByProjection(doc, DefinedViewportProjection.Right);

            case "back":
                return FindViewByProjection(doc, DefinedViewportProjection.Back);

            case "left":
                return FindViewByProjection(doc, DefinedViewportProjection.Left);

            case "bottom":
                return FindViewByProjection(doc, DefinedViewportProjection.Bottom);

            default:
                // Try to find view by name
                foreach (var view in doc.Views)
                {
                    if (view.ActiveViewport.Name?.Equals(viewportTarget, StringComparison.OrdinalIgnoreCase) == true)
                        return view;
                }
                return null;
        }
    }

    /// <summary>
    /// Finds a view by projection type, or temporarily reprojects the active view.
    /// The caller (CaptureViewport) is responsible for restoring viewport state.
    /// </summary>
    private RhinoView FindViewByProjection(RhinoDoc doc, DefinedViewportProjection projection)
    {
        string projectionName = projection.ToString();

        // First, try to find an existing view whose title matches the projection
        foreach (var view in doc.Views)
        {
            if (view.ActiveViewport.Name?.Equals(projectionName, StringComparison.OrdinalIgnoreCase) == true)
                return view;
        }

        // No dedicated view exists: temporarily reproject the active view (this also
        // renames it). CaptureViewport snapshots and restores both projection and name,
        // so the change is invisible to the user.
        var activeView = doc.Views.ActiveView;
        if (activeView != null)
        {
            activeView.ActiveViewport.SetProjection(projection, projectionName, false);
            doc.Views.Redraw();

            return activeView;
        }

        return doc.Views.ActiveView;
    }
}
