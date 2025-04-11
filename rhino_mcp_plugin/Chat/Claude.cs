using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.IO;
using System.Linq;
using Anthropic.SDK;
using Anthropic.SDK.Messaging;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;
using Rhino;

namespace RhinoMCPPlugin.Chat;

public class Claude
{
    private readonly AnthropicClient anthropic;
    private readonly List<ChatMessage> _chatMessages = new List<ChatMessage>();
    private IMcpClient _mcpClient;
    private IEnumerable<McpClientTool> _tools;
    private IChatClient _anthropicMcpClient;

    public Claude(string apiKey)
    {

        anthropic = new AnthropicClient(new APIAuthentication(apiKey));
        InitializeMcpClientAsync().GetAwaiter().GetResult();
        
    }

    private async Task InitializeMcpClientAsync()
    {
        try
        {
            var clientTransport = new StdioClientTransport(new()
            {
                Name = "Rhino MCP Server",
                Command = "uvx",
                Arguments = new List<string> {"rhinomcp"}
            });

            _mcpClient = await McpClientFactory.CreateAsync(clientTransport);
            _tools = await _mcpClient.ListToolsAsync();

            _anthropicMcpClient = anthropic.Messages
                .AsBuilder()
                .UseFunctionInvocation()
                .Build();
        }
        catch (Exception ex)
        {
            // Log error but continue with standard Claude API
            RhinoApp.WriteLine($"Failed to initialize MCP client: {ex.Message}");
        }
    }

    // Returning message
    public async Task<string> MessageAsync(string message)
    {
        // Add user message to history
        _chatMessages.Add(new ChatMessage { Role = "user", Content = message });

        string finalResponse;

        // Use MCP client if available
        if (_mcpClient != null && _tools != null && _anthropicMcpClient != null)
        {
            try
            {
                var options = new ChatOptions
                {
                    MaxOutputTokens = 1000,
                    ModelId = "claude-3-5-sonnet-20241022",
                    Tools = _tools.ToArray()
                };

                // Create the response using MCP tools
                var responseBuilder = new System.Text.StringBuilder();
                await foreach (var chunk in _anthropicMcpClient.GetStreamingResponseAsync(message, options))
                {
                    responseBuilder.Append(chunk);
                }
                finalResponse = responseBuilder.ToString();
            }
            catch (Exception ex)
            {
                // Fall back to standard API on error
                System.Diagnostics.Debug.WriteLine($"MCP client error: {ex.Message}. Falling back to standard API.");
                finalResponse = await FallbackToStandardAPI(message);
            }
        }
        else
        {
            // Use standard API if MCP client wasn't initialized
            finalResponse = await FallbackToStandardAPI(message);
        }

        // Add assistant response to chat history
        _chatMessages.Add(new ChatMessage { Role = "assistant", Content = finalResponse });

        return finalResponse;
    }

    private async Task<string> FallbackToStandardAPI(string message)
    {
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
        return response.Message;
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
