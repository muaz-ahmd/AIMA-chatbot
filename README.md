# AIMA ChatBot
> **Advanced Intelligent Multi-purpose Agent**

AIMA ChatBot is a powerful, hybrid conversational agent that combines **local pattern matching** for instant responses with **Google Gemini AI** for complex, intelligent reasoning. It is designed to be a lightweight, CLI-based assistant that runs efficiently on your local machine.

## 🚀 Features

*   **Hybrid Architecture**: Seamlessly switches between local logic (fast, offline-capable) and Cloud AI (smart, generative).
*   **Google Gemini 2.0 Integration**: Powered by the latest `gemini-2.0-flash` model for high-speed, cost-effective intelligence.
*   **CLI-First Design**: A professional command-line interface with ASCII art, clean formatting, and line-wrapping for optimal readability.
*   **Concise Responses**: Tuned to provide direct, no-fluff answers without unnecessary markdown or filler text.
*   **Extensive Configuration**: Fully customizable behavior via `config.py`.
*   **Robust Error Handling**: Auto-detects supported SDK versions and manages API connectivity issues gracefully.

## 🛠️ Prerequisites

*   **Python 3.8+** installed on your system.
*   A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/)).

## 📦 Installation

1.  **Clone the Repository** (or download the files to your folder):
    ```bash
    git clone <repository-url>
    cd AIMA-chatbot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is missing, ensure you have `google-genai` installed: `pip install google-genai`)*

3.  **Set Up API Key**:
    You can either set it as an environment variable (Recommended):
    ```bash
    # Windows PowerShell
    $env:GEMINI_API_KEY="your_api_key_here"
    ```
    Or paste it when prompted by the application.

## 💻 Usage

Run the chatbot using Python:

```bash
python main.py
```

### CLI Commands
*   `help` : Show the help menu.
*   `stats` : Display session statistics (token usage, local vs AI response count).
*   `config` : View current configuration settings.
*   `clear` : Clear the conversation history.
*   `quit` / `exit` : Close the application.

## ⚙️ Configuration

The bot is pre-configured for optimal performance, but you can customize it in `config.py`.

### Key Settings
*   **`gemini_model`**: Currently set to `gemini-2.0-flash`. You can change this to `gemini-1.5-pro` or others if needed.
*   **`system_instruction`**: Defines the persona of the bot. Currently set to be a "Helpful CLI assistant" that uses concise, plain text.
*   **`enable_local_priority`**: If `True`, the bot checks local patterns before calling the AI (saves quota).
*   **`max_history_length`**: Number of conversation turns to remember.

## 🔧 Troubleshooting

### "No supported generate interface available..."
This means your `google-genai` library is outdated or incompatible. The bot includes a fix for this in `gemini_client.py`. Ensure you have the latest version installed.

### "404 NOT_FOUND" (Model Error)
The configured model name is invalid for your API key.
*   Use the included script to check valid models: `python check_models.py`
*   Update `gemini_model` in `config.py` with a name from that list.

### "503 UNAVAILABLE"
The Google Gemini service is overloaded. Wait a moment and try again, or switch to a different model variant (e.g., from `flash` to `pro`) in `config.py`.