# AIMA ChatBot: Technical Overview & Functioning

This document provides a comprehensive look at the internal architecture and logic of the AIMA ChatBot. It is intended for developers or curious users who want to understand *how* the bot functions "under the hood."

## Core Architecture: The Hybrid Engine

The defining feature of AIMA is its **Hybrid Engine**. It does not rely solely on one source for intelligence. Instead, it uses a tiered approach to response generation:

1.  **Layer 1: Local Pattern Matching (The Reflex Layer)**
    *   **Function**: Handles common greetings, simple questions, and predefined functional commands immediately.
    *   **Mechanism**: Uses fuzzy string matching or Regex to compare user input against a local `patterns.json` database.
    *   **Benefit**: Zero latency, zero API cost, works offline.

2.  **Layer 2: Cloud AI (The Reasoning Layer)**
    *   **Function**: Handles complex queries, creative writing, coding tasks, and general knowledge.
    *   **Mechanism**: Uses the Google Gemini API (`google.genai` SDK).
    *   **Benefit**: Access to state-of-the-art Large Language Model (LLM) capabilities.

---

## 📂 Component Breakdown

### 1. `main.py` ( The Orchestrator)
*   **Role**: Entry point of the application.
*   **Key Responsibilities**:
    *   **Initialization**: Loads configuration and environment variables.
    *   **Session Loop**: Runs the `while True` input loop.
    *   **UI/UX**: Prints the ASCII banner, handle user commands (e.g., `quit`, `help`), and formats the output.
    *   **Formatting**: Implements strict line wrapping (80 chars) to ensure the text looks like a clean CLI tool.

### 2. `core/chatbot.py` (The Brain)
*   **Role**: The central logic controller.
*   **Logic Flow**:
    1.  Receives `user_input`.
    2.  **Check Local**: Queries the local pattern matcher. If a high-confidence match is found (>80%), it returns that response immediately.
    3.  **Check API**: If no local match is found, it forwards the request to the `GeminiClient`.
    4.  **History Management**: Appends the user message and the bot response to a history buffer to maintain conversational context (memory).

### 3. `ai/gemini_client.py` (The Connector)
*   **Role**: Interfaces with Google's GenAI servers.
*   **Key Logic**:
    *   **Dynamic SDK Detection**: It intelligently detects whether the user has the new `google.genai` SDK (v0.1+) or the legacy `google.generativeai` SDK and instantiates the correct client object.
    *   **Prompt Engineering**: It constructs the final payload sent to the AI.
        *   *System Instruction*: Prepended to every request: *"You are a helpful CLI assistant. Provide direct, concise answers..."*
        *   *Context*: Recent conversation history is appended so the AI "remembers" what you said previously.
    *   **Error Handling**: Catches network errors, 404s, or Rate Limits, and returns a safe fallback message instead of crashing.

### 4. `config.py` (The Control Panel)
*   **Role**: Centralized configuration using Python `dataclasses`.
*   **Settings**: Stores API keys, model names (`gemini-2.0-flash`), timeout settings, and style preferences.

---

## 🔄 Data Flow: Life of a Message

1.  **User types**: "How does Python garbage collection work?"
2.  **`main.py`** captures input.
3.  **`HybridChatbot`** checks `patterns.json` for "garbage collection".
    *   *Result*: No match found.
4.  **`HybridChatbot`** calls `gemini_client.generate_response`.
5.  **`gemini_client`** constructs the prompt:
    ```text
    System: You are a helpful CLI assistant... [Instructions]
    
    Context:
    User: Hi
    Bot: Hello!
    
    User: How does Python garbage collection work?
    ```
6.  **Google Gemini API** processes the prompt and returns a stream of text.
7.  **`gemini_client`** extracts clean text from the JSON response.
8.  **`main.py`** receives the text, wraps it to the terminal width, and prints it.

## 🛡️ Reliability Features

*   **SDK Compatibility**: The code includes a specific patch to handle the breaking changes between Google's old and new Python SDKs, ensuring the bot runs on almost any setup.
*   **Graceful Degradation**: If the internet cuts out or the API Key is invalid, the bot falls back to "Local Only" mode, serving only pattern responses instead of crashing.
