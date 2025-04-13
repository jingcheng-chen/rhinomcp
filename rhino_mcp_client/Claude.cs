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

namespace RhinoMCPClient;

public class Claude
{
    private readonly AnthropicClient anthropic;
    private readonly List<ChatMessage> _chatMessages = new ();
    private IMcpClient _mcpClient;
    private IEnumerable<McpClientTool> _tools;
    private IChatClient _anthropicMcpClient;
    public bool IsConnected { get; private set; }

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
                Arguments = new List<string> { "rhinomcp" }
            });

            _mcpClient = await McpClientFactory.CreateAsync(clientTransport);
            _tools = await _mcpClient.ListToolsAsync();

            _anthropicMcpClient = anthropic.Messages
                .AsBuilder()
                .UseFunctionInvocation()
                .Build();
            Console.WriteLine($"MCP Connection initialized.");
            IsConnected = true;
        }
        catch (Exception ex)
        {
            // Log error but continue with standard Claude API
            Console.WriteLine($"Failed to initialize MCP client: {ex.Message}");
            IsConnected = false;
        }
    }

    // Returning message
    public async Task<string> MessageAsync(string message)
    {
        // Add user message to history
        _chatMessages.Add(new ChatMessage(ChatRole.User, message));

    

        // Use MCP client if available
        if (_mcpClient == null || _tools == null || _anthropicMcpClient == null)
        {
            return "MCP client not initialized";
        }

        try
        {
            string finalResponse;
            var options = new ChatOptions
            {
                MaxOutputTokens = 1000,
                ModelId = "claude-3-5-sonnet-20241022",
                Tools = _tools.ToArray(),
            };

            // Create the response using MCP tools
            var responseBuilder = new System.Text.StringBuilder();
            await foreach (var chunk in _anthropicMcpClient.GetStreamingResponseAsync(_chatMessages, options))
            {
                responseBuilder.Append(chunk);
            }
            finalResponse = responseBuilder.ToString();
            // Add assistant response to chat history
            _chatMessages.Add(new ChatMessage(ChatRole.Assistant, finalResponse));
            return finalResponse;
        }
        catch (Exception ex)
        {
            // Fall back to standard API on error
            System.Diagnostics.Debug.WriteLine($"MCP client error: {ex.Message}. Falling back to standard API.");
            return "MCP client error: " + ex.Message;
        }
    }
    
    public void ClearHistory()
    {
        _chatMessages.Clear();
    }

}
