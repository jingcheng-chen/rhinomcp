using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    private static readonly string[] SetCameraFields = { "location", "target", "up", "lens_length", "projection" };

    // Point the named (or active) viewport's camera. ReadOnly so the dispatcher
    // opens no undo record: a view change is not a document edit, and undo must
    // keep reverting the last geometry change.
    [McpCommand("set_camera", ReadOnly = true)]
    public JObject SetCamera(JObject parameters)
    {
        if (!SetCameraFields.Any(field => IsGiven(parameters, field)))
            throw new McpException(
                McpException.InvalidArgument,
                "set_camera needs at least one of location, target, up, lens_length or projection",
                "Pass the camera fields to change; to frame objects use zoom_to instead.");

        var doc = RhinoDoc.ActiveDoc;
        var view = ResolveCameraView(doc, parameters);
        var viewport = view.ActiveViewport;

        if (IsGiven(parameters, "projection"))
        {
            string projection = castToString(parameters["projection"]);
            if (projection == "parallel")
            {
                if (!viewport.IsParallelProjection)
                    viewport.ChangeToParallelProjection(true);
            }
            else if (projection == "perspective")
            {
                if (!viewport.IsPerspectiveProjection)
                    viewport.ChangeToPerspectiveProjection(true, viewport.Camera35mmLensLength);
            }
            else
            {
                throw new McpException(
                    McpException.InvalidArgument,
                    $"Unknown projection '{projection}'",
                    "Pass projection \"perspective\" or \"parallel\".");
            }
        }

        if (IsGiven(parameters, "location") || IsGiven(parameters, "target"))
        {
            Point3d location = IsGiven(parameters, "location")
                ? castToPoint3d(parameters["location"])
                : viewport.CameraLocation;
            Point3d target = IsGiven(parameters, "target")
                ? castToPoint3d(parameters["target"])
                : viewport.CameraTarget;
            if (location.DistanceTo(target) < RhinoMath.ZeroTolerance)
                throw new McpException(
                    McpException.InvalidArgument,
                    "Camera location and target are the same point",
                    "Pass a location away from the target so the camera has a direction.");
            viewport.SetCameraLocations(target, location);
        }

        if (IsGiven(parameters, "up"))
        {
            double[] up = castToDoubleArray(parameters["up"]);
            var upVector = new Vector3d(up[0], up[1], up[2]);
            if (upVector.IsTiny() || upVector.IsParallelTo(viewport.CameraDirection) != 0)
                throw new McpException(
                    McpException.InvalidArgument,
                    "Camera up vector is zero or parallel to the view direction",
                    "Pass an up vector at an angle to the line from location to target, for example [0, 0, 1].");
            viewport.CameraUp = upVector;
        }

        if (IsGiven(parameters, "lens_length"))
        {
            double lens = castToDouble(parameters["lens_length"]);
            if (!(lens > 0))
                throw McpException.OutOfRange(
                    $"lens_length must be positive, got {lens}",
                    "Pass a 35 mm equivalent lens length in millimetres, for example 50.");
            viewport.Camera35mmLensLength = lens;
        }

        view.Redraw();
        return ViewportState(viewport);
    }

    // The named viewport (case-insensitive) or the active one. Never reprojects
    // a view to stand in for a missing name, unlike capture's GetTargetView.
    private static RhinoView ResolveCameraView(RhinoDoc doc, JObject parameters)
    {
        string name = parameters["viewport"]?.Type == JTokenType.String
            ? parameters["viewport"].ToString()
            : null;
        if (string.IsNullOrEmpty(name))
            return doc.Views.ActiveView ?? throw new McpException(
                McpException.NotFound, "No active viewport", "Open a model view in Rhino, then retry.");

        var view = doc.Views.FirstOrDefault(v =>
            string.Equals(v.ActiveViewport.Name, name, StringComparison.OrdinalIgnoreCase));
        return view ?? throw new McpException(
            McpException.NotFound,
            $"Viewport '{name}' not found",
            "Omit viewport to use the active one, or pass a viewport name such as Perspective, Top, Front or Right.");
    }
}
