# AIMA ChatBot
> **Advanced Intelligent Multi-purpose Agent**

AIMA ChatBot is a powerful, hybrid conversational agent that combines **local pattern matching** for instant responses with **Google Gemini AI** for complex, intelligent reasoning. It is designed to be a lightweight, CLI-based assistant that runs efficiently on your local machine.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Interface](https://img.shields.io/badge/Interface-CLI-green)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid-blueviolet)
![Status](https://img.shields.io/badge/Status-Active-success)


## 🚀 Features

*   **Hybrid Architecture**: Seamlessly switches between local logic (fast, offline-capable) and Cloud AI (smart, generative).
*   **Multi-Intent Handling**: Understands compound questions like "Hi! What time is it?" by splitting and combining responses.
*   **Long-Term User Memory**: Remembers facts about you across sessions (e.g., "My name is X") in user-specific profiles.
*   **Google Gemini 2.5 Integration**: Powered by the latest `gemini-2.5-flash` model for high-speed, cost-effective intelligence.
*   **CLI-First Design**: A professional command-line interface with ASCII art, clean formatting, and line-wrapping for optimal readability.
*   **Concise Responses**: Tuned to provide direct, no-fluff answers without unnecessary markdown or filler text.
*   **Extensive Configuration**: Fully customizable behavior via `config.py`.
*   **Robust Error Handling**: Auto-detects supported SDK versions and manages API connectivity issues gracefully.
*   **Smart Caching**: Caches only successful responses, not errors, ensuring reliable retry behavior.

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
    *(Note: If `requirements.txt` is missing, ensure you have `google-genai` and `fuzzywuzzy` installed)*

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

### User Profiles

By default, the bot uses your OS username to create a personal profile. To use a different identity:

```bash
python main.py --user=Alice
```

This creates `data/users/Alice.json` to store that user's memories separately.

### CLI Commands
*   `help` : Show the help menu.
*   `stats` : Display session statistics (token usage, local vs AI response count).
*   `config` : View current configuration settings.
*   `clear` : Clear the conversation history.
*   `train` : Manually teach the bot a new response pattern.
*   `autolearn [on/off]` : Toggle automatic learning from AI responses.
*   `quit` / `exit` : Close the application.

## ⚙️ Configuration

The bot is pre-configured for optimal performance, but you can customize it in `config.py`.

### Key Settings
*   **`gemini_model`**: Currently set to `gemini-2.5-flash`. You can change this to `gemini-2.0-flash-exp` or other available models if needed.
*   **`system_instruction`**: Defines the persona of the bot. Currently set to be a "Helpful CLI assistant" that uses concise, plain text.
*   **`enable_local_priority`**: If `True`, the bot checks local patterns before calling the AI (saves quota).
*   **`max_history_length`**: Number of conversation turns to remember.
*   **`enable_auto_learning`**: If `True`, the bot automatically learns new patterns from successful AI responses.

## 🔧 Troubleshooting

### "No supported generate interface available..."
This means your `google-genai` library is outdated or incompatible. The bot includes a fix for this in `gemini_client.py`. Ensure you have the latest version installed.

### "503 UNAVAILABLE"
The Google Gemini service is overloaded. Wait a moment and try again, or switch to a different model variant in `config.py`.

### Cached Error Messages
If the bot keeps returning the same error (e.g., "quota exceeded"), clear the cache by running the `clear` command or restart the bot.

## 📝 Recent Updates

### Bug Fixes
- Fixed import crashes when `google-genai` SDK is missing
- Added UTF-8 encoding to all file operations (Windows compatibility)
- Fixed regex generation for patterns ending in punctuation
- Prevented caching of error responses
- Added thread safety to response cache

### New Features
- **Multi-Intent Handling**: Answers compound questions by splitting on punctuation
- **Long-Term User Memory**: Remembers user facts across sessions with per-user profiles
- **User Identity**: Support for `--user` CLI argument to switch between profiles
