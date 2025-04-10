using System;
using Rhino;

namespace RhinoMCPPlugin.Chat;

public class ApiKeyManager
{
    private const string KEY_NAME = "ClaudeApiKey";

    public string GetApiKey()
    {

        return RhinoMCPPlugin.Instance.Settings.GetString(KEY_NAME, string.Empty);

    }

    public void SaveApiKey(string apiKey)
    {
        if (!string.IsNullOrEmpty(apiKey))
        {
            try
            {
                RhinoMCPPlugin.Instance.Settings.SetString(KEY_NAME, apiKey);
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"Error saving API key: {ex.Message}");
            }
        }
    }
}
