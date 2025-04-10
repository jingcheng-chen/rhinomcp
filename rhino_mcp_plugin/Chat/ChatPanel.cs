using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Eto.Drawing;
using Eto.Forms;
using Rhino.UI;

namespace RhinoMCPPlugin.Chat;

[System.Runtime.InteropServices.Guid("607da015-2ae4-43bd-a45d-294029353b02")]
public class ChatEtoPanel : Panel, IPanel
{
    readonly uint m_document_sn = 0;
    private readonly RichTextArea _conversationArea;
    private readonly TextArea _inputArea;
    private readonly Button _sendButton;
    private readonly Label _statusLabel;
    private bool _isStreaming = false;

    /// <summary>
    /// Provide easy access to the ChatEtoPanel.GUID
    /// </summary>
    public static System.Guid PanelId => typeof(ChatEtoPanel).GUID;

    /// <summary>
    /// Required public constructor with NO parameters
    /// </summary>
    public ChatEtoPanel(uint documentSerialNumber)
    {
        m_document_sn = documentSerialNumber;

        Title = "Rhino Chat";

        // Conversation display area
        _conversationArea = new RichTextArea
        {
            ReadOnly = true,
            BackgroundColor = Colors.White,
            Font = new Font("Arial", 10),
            Wrap = true
        };

        // User input area
        _inputArea = new TextArea
        {
            Height = 80,
            Font = new Font("Arial", 10),
            Wrap = true
        };
        _inputArea.KeyDown += InputArea_KeyDown;

        // Send button
        _sendButton = new Button { Text = "Send", Width = 80 };
        _sendButton.Click += SendButton_Click;

        // Status label
        _statusLabel = new Label { Text = "Ready", TextColor = Colors.Gray };

        // Layout
        var mainLayout = new DynamicLayout { DefaultPadding = new Padding(10), DefaultSpacing = new Size(5, 5) };

        // Add the conversation area with scrolling
        var conversationScroll = new Scrollable
        {
            Content = _conversationArea,
            ExpandContentWidth = true,
            Border = BorderType.None
        };
        mainLayout.Add(conversationScroll, true, true);

        // Add the input area and send button
        var inputLayout = new DynamicLayout { DefaultSpacing = new Size(5, 5) };
        inputLayout.BeginVertical();
        inputLayout.Add(_inputArea, true, true);

        var bottomLayout = new DynamicLayout { DefaultSpacing = new Size(5, 5) };
        bottomLayout.BeginHorizontal();
        bottomLayout.Add(_statusLabel, true);
        bottomLayout.Add(_sendButton);
        bottomLayout.EndHorizontal();

        inputLayout.Add(bottomLayout);
        inputLayout.EndVertical();

        mainLayout.Add(inputLayout, false);

        Content = mainLayout;

        // Add welcome message
        AddSystemMessage("Welcome to Rhino Chat. Type a message and press Send to start a conversation.");
    }

    private void InputArea_KeyDown(object sender, KeyEventArgs e)
    {
        // Send message when user presses Ctrl+Enter
        if (e.Key == Keys.Enter && e.Modifiers.HasFlag(Keys.Control))
        {
            SendMessage();
            e.Handled = true;
        }
    }

    private void SendButton_Click(object sender, EventArgs e)
    {
        SendMessage();
    }

    private void SendMessage()
    {
        if (_isStreaming || string.IsNullOrWhiteSpace(_inputArea.Text))
            return;

        string userMessage = _inputArea.Text.Trim();
        AddUserMessage(userMessage);
        _inputArea.Text = string.Empty;

        // Simulate LLM streaming response
        SimulateStreamingResponse(userMessage);
    }

    private void AddUserMessage(string message)
    {
        Application.Instance.Invoke(() =>
        {
            if (_conversationArea.Text.Length > 0)
                _conversationArea.Text += Environment.NewLine + Environment.NewLine;

            _conversationArea.Text += "You: " + message;
            _conversationArea.ScrollToEnd();
        });
    }

    private void AddAssistantMessage(string message)
    {
        Application.Instance.Invoke(() =>
        {
            if (_conversationArea.Text.Length > 0)
                _conversationArea.Text += Environment.NewLine + Environment.NewLine;

            _conversationArea.Text += "Assistant: " + message;
            _conversationArea.ScrollToEnd();
        });
    }

    private void AddSystemMessage(string message)
    {
        Application.Instance.Invoke(() =>
        {
            if (_conversationArea.Text.Length > 0)
                _conversationArea.Text += Environment.NewLine + Environment.NewLine;

            var currentText = _conversationArea.Text;
            _conversationArea.Text = currentText + "System: " + message;
            _conversationArea.ScrollToEnd();
        });
    }

    private async void SimulateStreamingResponse(string userInput)
    {
        try
        {
            _isStreaming = true;
            _sendButton.Enabled = false;
            _statusLabel.Text = "Assistant is thinking...";
            _statusLabel.TextColor = Colors.Orange;

            // Prepare for streaming response
            string responsePrefix = string.Empty;
            if (_conversationArea.Text.Length > 0)
                responsePrefix = Environment.NewLine + Environment.NewLine;

            responsePrefix += "Assistant: ";

            Application.Instance.Invoke(() =>
            {
                _conversationArea.Text += responsePrefix;
                _conversationArea.ScrollToEnd();
            });

            // This is just a placeholder - in a real implementation, 
            // you would connect to an actual LLM service
            string[] responseParts = GenerateDummyResponse(userInput);
            string fullResponse = string.Empty;

            foreach (var part in responseParts)
            {
                await Task.Delay(100); // Simulate network delay
                fullResponse += part;

                Application.Instance.Invoke(() =>
                {
                    var currentText = _conversationArea.Text;
                    _conversationArea.Text = currentText.Substring(0, currentText.Length - fullResponse.Length) + fullResponse;
                    _conversationArea.ScrollToEnd();
                });
            }

            _statusLabel.Text = "Ready";
            _statusLabel.TextColor = Colors.Gray;
        }
        catch (Exception ex)
        {
            _statusLabel.Text = "Error: " + ex.Message;
            _statusLabel.TextColor = Colors.Red;
        }
        finally
        {
            _isStreaming = false;
            _sendButton.Enabled = true;
        }
    }

    private string[] GenerateDummyResponse(string userInput)
    {
        // For testing/demonstration purposes only
        // This would be replaced with actual LLM integration
        string response = "I received your message. This is a simulated response to demonstrate the streaming functionality. In a real implementation, this would be connected to an LLM service.";

        // Split the response into small chunks to simulate streaming
        List<string> chunks = new List<string>();
        string[] words = response.Split(' ');

        for (int i = 0; i < words.Length; i++)
        {
            chunks.Add(words[i] + " ");
        }

        return chunks.ToArray();
    }

    public string Title { get; }

    #region IPanel methods
    public void PanelShown(uint documentSerialNumber, ShowPanelReason reason)
    {
        // Called when the panel tab is made visible
        Rhino.RhinoApp.WriteLine($"Chat panel shown for document {documentSerialNumber}");
    }

    public void PanelHidden(uint documentSerialNumber, ShowPanelReason reason)
    {
        // Called when the panel tab is hidden
        Rhino.RhinoApp.WriteLine($"Chat panel hidden for document {documentSerialNumber}");
    }

    public void PanelClosing(uint documentSerialNumber, bool onCloseDocument)
    {
        // Called when the document or panel container is closed/destroyed
        Rhino.RhinoApp.WriteLine($"Chat panel closing for document {documentSerialNumber}");
    }
    #endregion IPanel methods
}