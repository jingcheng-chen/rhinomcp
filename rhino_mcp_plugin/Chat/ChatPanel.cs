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
    private readonly Button _settingsButton;
    private readonly Button _clearButton;
    private readonly Label _statusLabel;
    private bool _isStreaming = false;
    private ClaudeConnector _claudeConnector;
    private readonly ApiKeyManager _apiKeyManager;

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
        _apiKeyManager = new ApiKeyManager();
        _claudeConnector = new ClaudeConnector(_apiKeyManager.GetApiKey());

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

        // Settings button (gear icon)
        _settingsButton = new Button
        {
            Text = "⚙", // Gear icon Unicode
            Width = 30,
            ToolTip = "API Settings"
        };
        _settingsButton.Click += async (sender, e) => await SettingsButton_Click(sender, e);

        // Clear button
        _clearButton = new Button
        {
            Text = "Clear",
            Width = 60,
            ToolTip = "Clear conversation"
        };
        _clearButton.Click += async (sender, e) => await ClearButton_Click(sender, e);

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
        bottomLayout.Add(_clearButton);
        bottomLayout.Add(_settingsButton);
        bottomLayout.Add(_sendButton);
        bottomLayout.EndHorizontal();

        inputLayout.Add(bottomLayout);
        inputLayout.EndVertical();

        mainLayout.Add(inputLayout, false);

        Content = mainLayout;

        // Add welcome message
        AddSystemMessage("Welcome to Rhino Chat. Type a message and press Send to start a conversation with Claude.");
    }

    private async Task SettingsButton_Click(object sender, EventArgs e)
    {
        var settingsDialog = new SettingsDialog(_apiKeyManager);
        var result = await settingsDialog.ShowModalAsync(this);

        if (result)
        {
            // Re-initialize Claude client with the new API key
            var response = await _claudeConnector.SetApiKey(_apiKeyManager.GetApiKey());
            AddSystemMessage(response);
        }
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

        // Use Claude API to get a response
        SendToClaudeAsync(userMessage);
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

            _conversationArea.Text += "Claude: " + message;
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

    private async void SendToClaudeAsync(string userInput)
    {
        try
        {
            _isStreaming = true;
            _sendButton.Enabled = false;
            _statusLabel.Text = "Claude is thinking...";
            _statusLabel.TextColor = Colors.Orange;

            var response = await _claudeConnector.SendMessage(userInput);

            // Use the AddAssistantMessage method instead of direct text manipulation
            AddAssistantMessage(response);

            _statusLabel.Text = "Ready";
            _statusLabel.TextColor = Colors.Gray;
        }
        catch (Exception ex)
        {
            _statusLabel.Text = "Error: " + ex.Message;
            _statusLabel.TextColor = Colors.Red;

            // Add error message to conversation with proper line breaks
            AddSystemMessage($"Error: {ex.Message}");
        }
        finally
        {
            _isStreaming = false;
            _sendButton.Enabled = true;
        }
    }

    private async Task ClearButton_Click(object sender, EventArgs e)
    {
        _conversationArea.Text = string.Empty;
        var response = await _claudeConnector.ClearHistory();
        AddSystemMessage(response);
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