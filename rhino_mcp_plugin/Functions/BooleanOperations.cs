using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoMCP.Shared.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Perform a boolean union on multiple objects.
    /// </summary>
    public JObject BooleanUnion(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();
        var deleteSources = parameters["delete_sources"]?.ToObject<bool>() ?? true;
        var name = parameters["name"]?.ToString();

        if (objectIds == null || objectIds.Count < 2)
            throw new ArgumentException("Boolean union requires at least 2 object IDs");

        var breps = new List<Brep>();
        var sourceObjects = new List<RhinoObject>();

        foreach (var idStr in objectIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null)
                throw new InvalidOperationException($"Object with ID {idStr} not found");

            sourceObjects.Add(obj);
            var brep = GetBrepFromObject(obj);
            if (brep != null)
                breps.Add(brep);
        }

        if (breps.Count < 2)
            throw new InvalidOperationException("Could not extract valid Breps from the provided objects");

        var results = Brep.CreateBooleanUnion(breps, RhinoDoc.ActiveDoc.ModelAbsoluteTolerance);

        if (results == null || results.Length == 0)
            throw new InvalidOperationException("Boolean union failed - objects may not intersect or be valid solids");

        // Delete source objects if requested
        if (deleteSources)
        {
            foreach (var obj in sourceObjects)
                doc.Objects.Delete(obj, true);
        }

        // Add result objects
        var resultIds = new JArray();
        foreach (var result in results)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(result, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = results.Length,
            ["message"] = $"Boolean union created {results.Length} object(s)"
        };
    }

    /// <summary>
    /// Perform a boolean difference (subtraction) operation.
    /// </summary>
    public JObject BooleanDifference(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var baseId = parameters["base_id"]?.ToString();
        var subtractIds = parameters["subtract_ids"]?.ToObject<List<string>>();
        var deleteSources = parameters["delete_sources"]?.ToObject<bool>() ?? true;
        var name = parameters["name"]?.ToString();

        if (string.IsNullOrEmpty(baseId))
            throw new ArgumentException("Boolean difference requires a base_id");

        if (subtractIds == null || subtractIds.Count == 0)
            throw new ArgumentException("Boolean difference requires at least one subtract_id");

        var baseObj = doc.Objects.Find(new Guid(baseId));
        if (baseObj == null)
            throw new InvalidOperationException($"Base object with ID {baseId} not found");

        var baseBreps = new List<Brep>();
        var baseBrep = GetBrepFromObject(baseObj);
        if (baseBrep != null)
            baseBreps.Add(baseBrep);
        else
            throw new InvalidOperationException("Could not extract valid Brep from base object");

        var subtractBreps = new List<Brep>();
        var subtractObjects = new List<RhinoObject>();

        foreach (var idStr in subtractIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null)
                throw new InvalidOperationException($"Object with ID {idStr} not found");

            subtractObjects.Add(obj);
            var brep = GetBrepFromObject(obj);
            if (brep != null)
                subtractBreps.Add(brep);
        }

        if (subtractBreps.Count == 0)
            throw new InvalidOperationException("Could not extract valid Breps from subtract objects");

        var results = Brep.CreateBooleanDifference(baseBreps, subtractBreps, RhinoDoc.ActiveDoc.ModelAbsoluteTolerance);

        if (results == null || results.Length == 0)
            throw new InvalidOperationException("Boolean difference failed - objects may not intersect or be valid solids");

        // Delete source objects if requested
        if (deleteSources)
        {
            doc.Objects.Delete(baseObj, true);
            foreach (var obj in subtractObjects)
                doc.Objects.Delete(obj, true);
        }

        // Add result objects
        var resultIds = new JArray();
        foreach (var result in results)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(result, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = results.Length,
            ["message"] = $"Boolean difference created {results.Length} object(s)"
        };
    }

    /// <summary>
    /// Perform a boolean intersection operation.
    /// </summary>
    public JObject BooleanIntersection(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();
        var deleteSources = parameters["delete_sources"]?.ToObject<bool>() ?? true;
        var name = parameters["name"]?.ToString();

        if (objectIds == null || objectIds.Count < 2)
            throw new ArgumentException("Boolean intersection requires at least 2 object IDs");

        var breps = new List<Brep>();
        var sourceObjects = new List<RhinoObject>();

        foreach (var idStr in objectIds)
        {
            var obj = doc.Objects.Find(new Guid(idStr));
            if (obj == null)
                throw new InvalidOperationException($"Object with ID {idStr} not found");

            sourceObjects.Add(obj);
            var brep = GetBrepFromObject(obj);
            if (brep != null)
                breps.Add(brep);
        }

        if (breps.Count < 2)
            throw new InvalidOperationException("Could not extract valid Breps from the provided objects");

        var results = Brep.CreateBooleanIntersection(breps[0], breps[1], RhinoDoc.ActiveDoc.ModelAbsoluteTolerance);

        // For more than 2 objects, chain intersections
        for (int i = 2; i < breps.Count && results != null && results.Length > 0; i++)
        {
            var newResults = new List<Brep>();
            foreach (var r in results)
            {
                var intersected = Brep.CreateBooleanIntersection(r, breps[i], RhinoDoc.ActiveDoc.ModelAbsoluteTolerance);
                if (intersected != null)
                    newResults.AddRange(intersected);
            }
            results = newResults.ToArray();
        }

        if (results == null || results.Length == 0)
            throw new InvalidOperationException("Boolean intersection failed - objects may not intersect or be valid solids");

        // Delete source objects if requested
        if (deleteSources)
        {
            foreach (var obj in sourceObjects)
                doc.Objects.Delete(obj, true);
        }

        // Add result objects
        var resultIds = new JArray();
        foreach (var result in results)
        {
            var attr = new ObjectAttributes();
            if (!string.IsNullOrEmpty(name))
                attr.Name = name;

            var id = doc.Objects.AddBrep(result, attr);
            resultIds.Add(id.ToString());
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["result_ids"] = resultIds,
            ["count"] = results.Length,
            ["message"] = $"Boolean intersection created {results.Length} object(s)"
        };
    }

    /// <summary>
    /// Helper to extract a Brep from various geometry types.
    /// </summary>
    private Brep GetBrepFromObject(RhinoObject obj)
    {
        if (obj.Geometry is Brep brep)
            return brep;

        if (obj.Geometry is Extrusion extrusion)
            return extrusion.ToBrep();

        if (obj.Geometry is Surface surface)
            return surface.ToBrep();

        return null;
    }
}
