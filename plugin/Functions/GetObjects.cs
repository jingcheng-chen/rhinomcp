using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("get_objects", ReadOnly = true)]
    public JObject GetObjects(JObject parameters)
    {
        const int DEFAULT_LIMIT = 50;
        const int MAX_LIMIT = 200;

        RhinoApp.WriteLine("Getting objects with filters...");
        var doc = RhinoDoc.ActiveDoc;

        // Parse parameters
        int offset = parameters["offset"]?.ToObject<int>() ?? 0;
        int limit = parameters["limit"]?.ToObject<int>() ?? DEFAULT_LIMIT;
        limit = Math.Min(limit, MAX_LIMIT);

        string layerFilter = parameters["layer_filter"]?.ToString();
        string typeFilter = parameters["type_filter"]?.ToString()?.ToUpper();
        JToken bboxFilter = parameters["bbox_filter"];
        bool includeGeometry = parameters["include_geometry"]?.ToObject<bool>() ?? true;
        bool selectedOnly = parameters["selected_only"]?.ToObject<bool>() ?? false;
        bool includeHidden = parameters["include_hidden"]?.ToObject<bool>() ?? false;
        bool includeLocked = parameters["include_locked"]?.ToObject<bool>() ?? true;

        // ids restrict the listing; ids not in the document are simply absent.
        HashSet<Guid> ids = null;
        if (parameters["ids"] is JArray idArray)
            ids = new HashSet<Guid>(idArray.Select(t => McpException.ParseGuid(t.ToString())));

        if (!string.IsNullOrEmpty(layerFilter) && FindLayerByNameOrFullPath(doc, layerFilter) == null)
            throw McpException.LayerNotFound(layerFilter);

        // Parse bbox filter if provided
        BoundingBox? filterBbox = null;
        if (bboxFilter != null)
        {
            try
            {
                var bboxArray = bboxFilter.ToObject<double[][]>();
                if (bboxArray != null && bboxArray.Length == 2)
                {
                    var min = new Point3d(bboxArray[0][0], bboxArray[0][1], bboxArray[0][2]);
                    var max = new Point3d(bboxArray[1][0], bboxArray[1][1], bboxArray[1][2]);
                    filterBbox = new BoundingBox(min, max);
                }
            }
            catch
            {
                RhinoApp.WriteLine("Invalid bbox_filter format");
            }
        }

        // Build filtered object list
        var allObjects = new List<RhinoObject>();

        // The default enumerator lists normal and locked objects, not hidden
        // ones; include_hidden widens it, and the rest narrow it below.
        IEnumerable<RhinoObject> candidates = includeHidden
            ? doc.Objects.GetObjectList(new ObjectEnumeratorSettings { HiddenObjects = true })
            : doc.Objects;

        foreach (var obj in candidates)
        {
            if (!includeLocked && (obj.IsLocked || doc.Layers[obj.Attributes.LayerIndex].IsLocked))
                continue;
            if (selectedOnly && obj.IsSelected(false) == 0)
                continue;
            if (ids != null && !ids.Contains(obj.Id))
                continue;

            // Layer filter
            if (!string.IsNullOrEmpty(layerFilter))
            {
                var layer = doc.Layers[obj.Attributes.LayerIndex];
                string objLayerName = layer.Name;
                string objLayerFullPath = layer.FullPath;

                // Match by name or full path (case-insensitive)
                if (!objLayerName.Equals(layerFilter, StringComparison.OrdinalIgnoreCase) &&
                    !objLayerFullPath.Equals(layerFilter, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
            }

            // Type filter
            if (!string.IsNullOrEmpty(typeFilter))
            {
                string objType = GetNormalizedType(obj);
                if (!objType.Equals(typeFilter, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
            }

            // Bounding box filter
            if (filterBbox.HasValue)
            {
                BoundingBox objBbox = obj.Geometry.GetBoundingBox(true);
                // Object passes if its bbox intersects with the filter bbox
                if (!filterBbox.Value.Contains(objBbox.Center) &&
                    !BoundingBoxIntersects(filterBbox.Value, objBbox))
                {
                    continue;
                }
            }

            allObjects.Add(obj);
        }

        int totalMatching = allObjects.Count;

        // Apply pagination
        var pagedObjects = allObjects
            .Skip(offset)
            .Take(limit)
            .ToList();

        // Serialize objects
        var objectsArray = new JArray();
        foreach (var obj in pagedObjects)
        {
            if (includeGeometry)
            {
                objectsArray.Add(Serializer.RhinoObject(obj));
            }
            else
            {
                // Lightweight version without geometry details
                var objDoc = obj.Document ?? RhinoDoc.ActiveDoc;
                objectsArray.Add(new JObject
                {
                    ["id"] = obj.Id.ToString(),
                    ["name"] = obj.Name ?? "(unnamed)",
                    ["type"] = GetNormalizedType(obj),
                    ["layer"] = objDoc.Layers[obj.Attributes.LayerIndex].Name,
                    ["bounding_box"] = Serializer.SerializeBBox(obj.Geometry.GetBoundingBox(true))
                });
            }
        }

        var result = new JObject
        {
            ["objects"] = objectsArray,
            ["total_matching"] = totalMatching,
            ["offset"] = offset,
            ["limit"] = limit,
            ["has_more"] = offset + pagedObjects.Count < totalMatching
        };

        // Include applied filters in response for clarity
        var appliedFilters = new JObject();
        if (!string.IsNullOrEmpty(layerFilter)) appliedFilters["layer"] = layerFilter;
        if (!string.IsNullOrEmpty(typeFilter)) appliedFilters["type"] = typeFilter;
        if (filterBbox.HasValue) appliedFilters["bbox"] = Serializer.SerializeBBox(filterBbox.Value);
        if (ids != null) appliedFilters["id_count"] = ids.Count;
        if (selectedOnly) appliedFilters["selected_only"] = true;
        if (includeHidden) appliedFilters["include_hidden"] = true;
        if (!includeLocked) appliedFilters["include_locked"] = false;
        if (appliedFilters.Count > 0) result["filters"] = appliedFilters;

        RhinoApp.WriteLine($"GetObjects: returned {pagedObjects.Count} of {totalMatching} matching objects");
        return result;
    }

    private bool BoundingBoxIntersects(BoundingBox a, BoundingBox b)
    {
        return a.Min.X <= b.Max.X && a.Max.X >= b.Min.X &&
               a.Min.Y <= b.Max.Y && a.Max.Y >= b.Min.Y &&
               a.Min.Z <= b.Max.Z && a.Max.Z >= b.Min.Z;
    }
}
