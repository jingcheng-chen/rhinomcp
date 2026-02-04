using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Captures a viewport screenshot and returns it as base64-encoded PNG data.
    /// </summary>
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

        // Find the target view
        RhinoView targetView = GetTargetView(doc, viewportTarget);
        if (targetView == null)
        {
            throw new InvalidOperationException($"Viewport '{viewportTarget}' not found. Available viewports: Perspective, Top, Front, Right, Back, Left, Bottom, or use 'active' for the current view.");
        }

        // Store viewport name
        string viewportName = targetView.ActiveViewport.Name ?? viewportTarget;

        // Apply zoom to fit if requested
        if (zoomToFit && doc.Objects.Count > 0)
        {
            targetView.ActiveViewport.ZoomExtents();
            doc.Views.Redraw();
        }

        // Capture the bitmap
        Size captureSize = new Size(width, height);
        Bitmap bitmap = targetView.CaptureToBitmap(captureSize, showGrid, showAxes, showCplaneAxes);

        if (bitmap == null)
        {
            throw new InvalidOperationException("Failed to capture viewport bitmap. The viewport may be minimized or hidden.");
        }

        // Convert bitmap to base64 PNG
        string base64Data;
        try
        {
            using (MemoryStream ms = new MemoryStream())
            {
                bitmap.Save(ms, ImageFormat.Png);
                byte[] imageBytes = ms.ToArray();
                base64Data = Convert.ToBase64String(imageBytes);
            }
        }
        finally
        {
            bitmap.Dispose();
        }

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
            ["object_count"] = doc.Objects.Count
        };
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
    /// Finds a view by projection type, or temporarily sets the active view to that projection.
    /// </summary>
    private RhinoView FindViewByProjection(RhinoDoc doc, DefinedViewportProjection projection)
    {
        string projectionName = projection.ToString();

        // First, try to find existing view with matching name
        foreach (var view in doc.Views)
        {
            if (view.ActiveViewport.Name?.Equals(projectionName, StringComparison.OrdinalIgnoreCase) == true)
                return view;
        }

        // If not found by name, use the active view and temporarily set the projection
        var activeView = doc.Views.ActiveView;
        if (activeView != null)
        {
            // Store original state
            var originalProjection = activeView.ActiveViewport.IsParallelProjection;

            // Set the desired projection
            activeView.ActiveViewport.SetProjection(projection, projectionName, false);
            doc.Views.Redraw();

            return activeView;
        }

        return doc.Views.ActiveView;
    }
}
