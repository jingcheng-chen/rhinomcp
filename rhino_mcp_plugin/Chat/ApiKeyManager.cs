using System;

namespace RhinoMCPPlugin.Chat
{
    public class ApiKeyManager
    {
        // Default API key
        private string _apiKey = "";

        public string GetApiKey()
        {
            return _apiKey;
        }

        public void SaveApiKey(string apiKey)
        {
            if (!string.IsNullOrEmpty(apiKey))
                _apiKey = apiKey;
        }
    }
}