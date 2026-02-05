using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoMCP.Shared.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject CreateObjects(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var results = new JObject();
        int successCount = 0;
        int failureCount = 0;
        var errors = new JArray();

        // Process each object in the parameters
        foreach (var property in parameters.Properties())
        {
            try
            {
                // Get the object parameters
                JObject objectParams = (JObject)property.Value;

                // Create the object using the existing CreateObject method
                JObject result = CreateObject(objectParams);

                // Add the result to our results collection
                results[property.Name] = result;
                successCount++;
            }
            catch (Exception ex)
            {
                // If there's an error creating this object, add the error to the results
                results[property.Name] = new JObject
                {
                    ["status"] = "error",
                    ["error"] = ex.Message
                };
                errors.Add(new JObject
                {
                    ["name"] = property.Name,
                    ["error"] = ex.Message
                });
                failureCount++;
            }
        }

        // Update views
        doc.Views.Redraw();

        return new JObject
        {
            ["objects"] = results,
            ["success_count"] = successCount,
            ["failure_count"] = failureCount,
            ["total"] = successCount + failureCount,
            ["errors"] = errors
        };
    }
}