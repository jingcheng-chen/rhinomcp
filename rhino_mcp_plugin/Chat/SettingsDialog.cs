using System;
using Eto.Drawing;
using Eto.Forms;

namespace RhinoMCPPlugin.Chat
{
    public class SettingsDialog : Dialog<bool>
    {
        private readonly TextBox _apiKeyTextBox;
        private readonly ApiKeyManager _apiKeyManager;

        public SettingsDialog(ApiKeyManager apiKeyManager)
        {
            _apiKeyManager = apiKeyManager;

            Title = "Claude API Settings";
            MinimumSize = new Size(400, 200);
            Padding = new Padding(10);

            // Create layout
            var layout = new DynamicLayout { DefaultPadding = new Padding(10), DefaultSpacing = new Size(5, 5) };

            // API Key section
            layout.Add(new Label { Text = "Claude API Key:", Font = new Font(SystemFont.Bold) });
            _apiKeyTextBox = new TextBox
            {
                Text = _apiKeyManager.GetApiKey() ?? string.Empty
                // Note: Using a standard TextBox as Eto.Forms doesn't support password masking directly
            };
            layout.Add(_apiKeyTextBox);

            // Add note about API key security
            layout.Add(new Label
            {
                Text = "Note: Your API key is stored locally and never shared.",
                TextColor = Colors.Gray
            });

            // Buttons
            var buttonLayout = new DynamicLayout { DefaultSpacing = new Size(5, 5) };
            buttonLayout.BeginHorizontal();
            buttonLayout.Add(null, true); // Spacer

            var cancelButton = new Button { Text = "Cancel" };
            cancelButton.Click += (sender, e) => Close(false);

            var saveButton = new Button { Text = "Save" };
            saveButton.Click += SaveButton_Click;

            buttonLayout.Add(cancelButton);
            buttonLayout.Add(saveButton);
            buttonLayout.EndHorizontal();

            layout.Add(null, true); // Spacer
            layout.Add(buttonLayout);

            Content = layout;
        }

        private void SaveButton_Click(object sender, EventArgs e)
        {
            string apiKey = _apiKeyTextBox.Text.Trim();
            if (string.IsNullOrEmpty(apiKey))
            {
                MessageBox.Show("Please enter a valid API key.", "Error", MessageBoxType.Error);
                return;
            }

            _apiKeyManager.SaveApiKey(apiKey);
            Close(true);
        }
    }
}