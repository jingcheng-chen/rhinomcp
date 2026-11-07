using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Display;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Captures a viewport screenshot as base64 PNG or JPEG data plus metadata saying what it shows.
    /// Display mode, camera, lens and framing are temporary and restored in the finally block.
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

        // Temporary view state for this capture only. Everything is validated
        // before any view is touched, so a refusal leaves the views alone.
        var request = ParseCaptureRequest(doc, parameters);

        // Refreshing display caches can also adjust clipping/camera state in views
        // other than the capture target. Snapshot every view before any refresh or
        // temporary projection change, and restore without triggering another redraw.
        var savedViews = doc.Views.Select(view => new
        {
            View = view,
            Projection = new ViewportInfo(view.ActiveViewport),
            Name = view.ActiveViewport.Name,
            Target = view.ActiveViewport.CameraTarget,
            DisplayMode = view.ActiveViewport.DisplayMode
        }).ToArray();

        try
        {
            RhinoView targetView = GetTargetView(doc, viewportTarget);
            if (targetView == null)
                throw new InvalidOperationException($"Viewport '{viewportTarget}' not found. Available viewports: Perspective, Top, Front, Right, Back, Left, Bottom, or use 'active' for the current view.");
            var viewport = targetView.ActiveViewport;

            if (request.DisplayMode != null && viewport.DisplayMode?.Id != request.DisplayMode.Id)
                viewport.DisplayMode = request.DisplayMode;

            // Refresh the current document display before capturing.
            doc.Views.Redraw();
            // Rhino queues redraws on Mac. Finish them before fitting/restoring;
            // otherwise a queued redraw changes cameras after this method returns.
            RhinoApp.Wait();

            // Store viewport name
            string viewportName = viewport.Name ?? viewportTarget;

            ApplyCaptureCamera(viewport, request);

            // Count active objects, not doc.Objects.Count, which also counts
            // undoable-deleted entries.
            int activeCount = CountActiveObjects(doc);
            if (request.Frame.HasValue)
            {
                // Same fit as zoom_to_fit, on a copy of the view state, aimed at
                // the requested box (padded when degenerate); it takes precedence
                // over zoom_to_fit.
                var framed = PadForFraming(request.Frame.Value);
                FitCaptureProjection(viewport, width, height,
                    fitted => fitted.DollyExtents(framed, 1.1));
            }
            else if (zoomToFit && activeCount > 0)
            {
                // ZoomExtents fits the on-screen aspect ratio. CaptureToBitmap uses
                // the requested aspect instead, which can crop a previously fitted
                // model. Fit a temporary projection to the output dimensions first.
                // A degenerate union (one point, or everything in one plane) is
                // fitted as a padded box, since DollyExtents fails on it.
                var visibleGeometry = VisibleObjects(doc, viewport).Select(obj => obj.Geometry).ToArray();
                var visibleBox = BoundingBox.Empty;
                foreach (var geometry in visibleGeometry)
                    visibleBox.Union(geometry.GetBoundingBox(true));
                if (visibleBox.IsValid)
                {
                    var framed = PadForFraming(visibleBox);
                    bool degenerate = framed.Diagonal != visibleBox.Diagonal;
                    FitCaptureProjection(viewport, width, height, fitted => degenerate
                        ? fitted.DollyExtents(framed, 1.1)
                        : fitted.DollyExtents(visibleGeometry, 1.1));
                }
            }

            string base64Data = CaptureViewToPngBase64(
                targetView,
                width,
                height,
                showGrid,
                showAxes,
                showCplaneAxes,
                "capture_viewport",
                request.Jpeg ? ImageFormat.Jpeg : ImageFormat.Png);

            RhinoApp.WriteLine($"Captured viewport '{viewportName}' ({width}x{height})");

            // Metadata is read from the viewport as it was rendered, before restore.
            var sceneBbox = BoundingBox.Empty;
            foreach (var obj in doc.Objects)
                sceneBbox.Union(obj.Geometry.GetBoundingBox(true));
            int visibleCount = VisibleObjects(doc, viewport)
                .Count(obj => viewport.IsVisible(obj.Geometry.GetBoundingBox(true)));

            var result = new JObject
            {
                ["image_data"] = base64Data,
                ["mime_type"] = request.Jpeg ? "image/jpeg" : "image/png",
                ["width"] = width,
                ["height"] = height,
                ["viewport_name"] = viewportName,
                ["viewport_target"] = viewportTarget,
                ["show_grid"] = showGrid,
                ["show_axes"] = showAxes,
                ["show_cplane_axes"] = showCplaneAxes,
                ["object_count"] = activeCount,
                ["scene_bounding_box"] = SerializeMinMax(sceneBbox),
                ["visible_object_count"] = visibleCount,
                ["total_object_count"] = activeCount
            };
            foreach (var field in ViewportState(viewport).Properties())
            {
                // viewport_name keeps the name captured before any reprojection.
                if (field.Name != "viewport_name")
                    result[field.Name] = field.Value;
            }
            return result;
        }
        finally
        {
            // Projection carries camera location, direction, up, frustum, lens
            // and parallel/perspective; display mode and name are restored apart.
            foreach (var saved in savedViews)
            {
                using (saved.Projection)
                {
                    var viewport = saved.View.ActiveViewport;
                    viewport.SetViewProjection(saved.Projection, false);
                    viewport.SetCameraTarget(saved.Target, false);
                    if (viewport.Name != saved.Name)
                        viewport.Name = saved.Name;
                    if (saved.DisplayMode != null && viewport.DisplayMode?.Id != saved.DisplayMode.Id)
                        viewport.DisplayMode = saved.DisplayMode;
                }
            }
        }
    }

    private sealed class CaptureRequest
    {
        public DisplayModeDescription DisplayMode;
        public Point3d? CameraLocation;
        public Point3d? CameraTarget;
        public double? LensLength;
        public BoundingBox? Frame;
        public bool Jpeg;
    }

    private CaptureRequest ParseCaptureRequest(RhinoDoc doc, JObject parameters)
    {
        var request = new CaptureRequest();

        string format = parameters["format"]?.ToString()?.ToLowerInvariant() ?? "png";
        if (format != "png" && format != "jpeg")
            throw McpException.OutOfRange($"Unknown image format '{format}'", "Pass format \"png\" or \"jpeg\".");
        request.Jpeg = format == "jpeg";

        var frameIds = parameters["frame_object_ids"] as JArray;
        var frameBbox = parameters["frame_bbox"] as JObject;
        bool zoomToFit = parameters["zoom_to_fit"]?.ToObject<bool>() ?? false;
        bool hasLens = parameters["lens_length"] != null && parameters["lens_length"].Type != JTokenType.Null;
        bool hasCamera = parameters["camera_location"] is JArray || parameters["camera_target"] is JArray || hasLens;
        if (hasCamera && (frameIds != null || frameBbox != null || zoomToFit))
            throw new McpException(McpException.InvalidArgument,
                "An explicit camera (camera_location, camera_target, lens_length) cannot be combined with framing (frame_object_ids, frame_bbox, zoom_to_fit)",
                "Pass camera_location, camera_target or lens_length to look from a known point, or frame_object_ids, frame_bbox or zoom_to_fit to frame geometry, not both.");

        string modeName = parameters["display_mode"]?.ToString();
        if (modeName != null)
        {
            var modes = DisplayModeDescription.GetDisplayModes();
            request.DisplayMode = modes.FirstOrDefault(m =>
                string.Equals(m.EnglishName, modeName, StringComparison.OrdinalIgnoreCase)
                || string.Equals(m.LocalName, modeName, StringComparison.OrdinalIgnoreCase));
            if (request.DisplayMode == null)
                throw new McpException(McpException.InvalidArgument,
                    $"Display mode '{modeName}' not found",
                    "Use one of the available display modes: " + string.Join(", ", modes.Select(m => m.EnglishName)) + ".");
        }

        if (parameters["camera_location"] is JArray)
            request.CameraLocation = castToPoint3d(parameters["camera_location"]);
        if (parameters["camera_target"] is JArray)
            request.CameraTarget = castToPoint3d(parameters["camera_target"]);
        if (request.CameraLocation.HasValue && request.CameraTarget.HasValue
            && request.CameraLocation.Value.DistanceTo(request.CameraTarget.Value) < RhinoMath.ZeroTolerance)
            throw McpException.OutOfRange("camera_location and camera_target are the same point",
                "Place the camera away from its target, for example 100 units back along the view direction.");

        if (hasLens)
        {
            double lens = parameters["lens_length"].ToObject<double>();
            if (lens <= 0)
                throw McpException.OutOfRange($"lens_length must be positive, got {lens}",
                    "Pass a 35mm-equivalent lens length in millimetres, for example 50.");
            request.LensLength = lens;
        }

        if (frameIds != null)
        {
            var box = BoundingBox.Empty;
            foreach (var token in frameIds)
            {
                var obj = doc.Objects.Find(McpException.ParseGuid(token.ToString()))
                    ?? throw McpException.ObjectNotFound(token.ToString());
                box.Union(obj.Geometry.GetBoundingBox(true));
            }
            request.Frame = box;
        }
        else if (frameBbox != null)
        {
            var box = new BoundingBox(castToPoint3d(frameBbox["min"]), castToPoint3d(frameBbox["max"]));
            if (!box.IsValid)
                throw McpException.OutOfRange("frame_bbox min must not exceed max on any axis",
                    "Pass frame_bbox as {\"min\": [x, y, z], \"max\": [x, y, z]} with min <= max.");
            request.Frame = box;
        }
        if (request.Frame.HasValue && !request.Frame.Value.IsValid)
            throw McpException.OutOfRange("The framed objects have no bounding box",
                "Frame objects with geometry, or pass frame_bbox instead.");

        return request;
    }

    private static void ApplyCaptureCamera(RhinoViewport viewport, CaptureRequest request)
    {
        if (request.LensLength.HasValue && viewport.IsPerspectiveProjection)
            viewport.Camera35mmLensLength = request.LensLength.Value;
        if (request.CameraLocation.HasValue || request.CameraTarget.HasValue)
        {
            var location = request.CameraLocation ?? viewport.CameraLocation;
            var target = request.CameraTarget ?? viewport.CameraTarget;
            viewport.SetCameraLocations(target, location);
        }
    }

    private static void FitCaptureProjection(RhinoViewport viewport, int width, int height,
        Func<ViewportInfo, bool> fit)
    {
        using var fitted = new ViewportInfo(viewport);
        fitted.FrustumAspect = (double)width / height;
        if (!fit(fitted) || !viewport.SetViewProjection(fitted, true))
            throw new InvalidOperationException("Could not fit geometry to capture dimensions.");
    }

    private static IEnumerable<RhinoObject> VisibleObjects(RhinoDoc doc, RhinoViewport viewport) =>
        doc.Objects.GetObjectList(new ObjectEnumeratorSettings
        {
            VisibleFilter = true,
            ViewportFilter = viewport,
            NormalObjects = true,
            LockedObjects = true
        });

    [SuppressMessage("Interoperability", "CA1416:Validate platform compatibility",
        Justification = "Runs in the Rhino process which provides cross-platform System.Drawing support.")]
    private static string CaptureViewToPngBase64(
        RhinoView targetView,
        int width,
        int height,
        bool showGrid,
        bool showAxes,
        bool showCplaneAxes,
        string commandName,
        ImageFormat format = null)
    {
        format ??= ImageFormat.Png;
        Size captureSize = new Size(width, height);
        Bitmap bitmap = targetView.CaptureToBitmap(captureSize, showGrid, showAxes, showCplaneAxes);
        if (bitmap == null)
        {
            throw new InvalidOperationException("Failed to capture viewport bitmap. The viewport may be minimized or hidden.");
        }

        try
        {
            using MemoryStream ms = new MemoryStream();
            bitmap.Save(ms, format);
            byte[] imageBytes = ms.ToArray();
            return Convert.ToBase64String(imageBytes);
        }
        catch (PlatformNotSupportedException ex)
        {
            throw new InvalidOperationException(
                $"{commandName}: {format} encoding is not supported on this platform. " +
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

            return activeView;
        }

        return doc.Views.ActiveView;
    }
}
