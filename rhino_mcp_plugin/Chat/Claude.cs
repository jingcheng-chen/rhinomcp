using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Anthropic.SDK;
using Anthropic.SDK.Messaging;

namespace RhinoMCPPlugin.Chat;

public class Claude
{
    private readonly AnthropicClient anthropic;
    private readonly List<ChatMessage> _chatMessages = new List<ChatMessage>();

    public Claude(string apiKey)
    {
        anthropic = new AnthropicClient(new APIAuthentication(apiKey));
    }

    // Returning message
    public async Task<string> MessageAsync(string message)
    {
        // Add user message to history
        _chatMessages.Add(new ChatMessage { Role = "user", Content = message });

        // Create messages list with the conversation history
        var messages = new List<Message>();

        // Add previous conversation context (limit to last 10 messages to avoid token limits)
        int startIdx = Math.Max(0, _chatMessages.Count - 11);  // -11 to keep space for the new user message
        for (int i = startIdx; i < _chatMessages.Count - 1; i++)
        {
            var chatMsg = _chatMessages[i];
            var roleType = chatMsg.Role.ToLower() == "user" ? RoleType.User : RoleType.Assistant;
            messages.Add(new Message(roleType, chatMsg.Content));
        }

        // Add the current user message
        messages.Add(new Message(RoleType.User, message));

        // Create message parameters
        var parameters = new MessageParameters
        {
            Messages = messages,
            MaxTokens = 1000,
            Temperature = 0.7m,
            Model = "claude-3-5-sonnet-20241022"
        };

        var response = await anthropic.Messages
            .GetClaudeMessageAsync(parameters);
        var finalResponse = response.Message;

        // Add assistant response to chat history
        _chatMessages.Add(new ChatMessage { Role = "assistant", Content = finalResponse });

        return finalResponse;
    }


    // Streaming implementation with Server-Sent Events
    // public async Task<string> StreamMessageAsync(string message, Action<string> onChunk)
    // {
    //     // Add user message to history
    //     _chatMessages.Add(new ChatMessage { Role = "user", Content = message });
    //     var fullResponse = "";
    //     
    //     Message[] messages = new []{new Message() { Role = "user", Content = message }};
    //
    //     var stream = anthropic.Messages.CreateStreamAsync(new()
    //     {
    //         Model = CLAUDE_MODEL,
    //         MaxTokens = 1024,
    //         Messages = messages
    //     });
    //
    //     await foreach (var messageStreamEvent in stream)
    //     {
    //         if (messageStreamEvent is ContentBlockDelta content)
    //         {
    //             onChunk(content.Delta.Text);
    //             fullResponse += content.Delta.Text;
    //         }
    //     }
    //
    //     var finalResponse = fullResponse;
    //     // Add assistant response to chat history
    //     _chatMessages.Add(new ChatMessage { Role = "claude", Content = finalResponse });
    //
    //     return finalResponse;
    // }

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
