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

        foreach (var obj in doc.Objects)
        {
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
