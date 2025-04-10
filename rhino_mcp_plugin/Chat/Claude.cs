using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Claudia;

namespace RhinoMCPPlugin.Chat;

public class Claude
{
    private readonly string _apiKey;
    private readonly Anthropic anthropic;
    private readonly List<ChatMessage> _chatMessages = new List<ChatMessage>();

    private const string CLAUDE_MODEL = "Claude3_7Sonnet";

    public Claude(string apiKey)
    {
        anthropic = new Anthropic
        {
            ApiKey = apiKey
        };
    }

    

    // Streaming implementation with Server-Sent Events
    public async Task<string> StreamMessageAsync(string message, Action<string> onChunk)
    {
        // Add user message to history
        _chatMessages.Add(new ChatMessage { Role = "user", Content = message });
        var fullResponse = "";
        
        Message[] messages = new []{new Message() { Role = "user", Content = message }};

        var stream = anthropic.Messages.CreateStreamAsync(new()
        {
            Model = CLAUDE_MODEL,
            MaxTokens = 1024,
            Messages = messages
        });

        await foreach (var messageStreamEvent in stream)
        {
            if (messageStreamEvent is ContentBlockDelta content)
            {
                onChunk(content.Delta.Text);
                fullResponse += content.Delta.Text;
            }
        }

        var finalResponse = fullResponse;
        // Add assistant response to chat history
        _chatMessages.Add(new ChatMessage { Role = "claude", Content = finalResponse });

        return finalResponse;
    }

    public void ClearHistory()
    {
        _chatMessages.Clear();
    }

    // Simple class to represent a chat message
    public class ChatMessage
    {
        public string Role { get; set; }
        public string Content { get; set; }
    }
}
