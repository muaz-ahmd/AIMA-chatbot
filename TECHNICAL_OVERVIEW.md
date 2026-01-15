# AIMA ChatBot: Technical Overview & Functioning

This document provides a comprehensive look at the internal architecture and logic of the AIMA ChatBot. It is intended for developers or curious users who want to understand *how* the bot functions "under the hood."

## Core Architecture: The Hybrid Engine

The defining feature of AIMA is its **Hybrid Engine**. It does not rely solely on one source for intelligence. Instead, it uses a tiered approach to response generation:

1.  **Layer 1: Local Pattern Matching (The Reflex Layer)**
    *   **Function**: Handles common greetings, simple questions, and predefined functional commands immediately.
    *   **Mechanism**: Uses fuzzy string matching or Regex to compare user input against a local `patterns.json` database.
    *   **Benefit**: Zero latency, zero API cost, works offline.
    *   **Enhancement**: Now supports **Multi-Intent Splitting** - can answer compound questions like "Hi! Thanks!" by combining multiple pattern matches.

2.  **Layer 2: Cloud AI (The Reasoning Layer)**
    *   **Function**: Handles complex queries, creative writing, coding tasks, and general knowledge.
    *   **Mechanism**: Uses the Google Gemini API (`google.genai` SDK) with `gemini-2.5-flash`.
    *   **Benefit**: Access to state-of-the-art Large Language Model (LLM) capabilities.
    *   **Enhancement**: **User Context Injection** - AI receives user profile information for personalized responses.

3.  **Layer 3: Long-Term Memory (The Persistence Layer)**
    *   **Function**: Stores user-specific facts across sessions.
    *   **Mechanism**: User profiles saved in `data/users/{username}.json`.
    *   **Benefit**: The bot "remembers" information like your name, preferences, etc.

---

## 📂 Component Breakdown

### 1. `main.py` (The Orchestrator)
*   **Role**: Entry point of the application.
*   **Key Responsibilities**:
    *   **Initialization**: Loads configuration and environment variables.
    *   **Session Loop**: Runs the `while True` input loop.
    *   **UI/UX**: Prints the ASCII banner, handles user commands (e.g., `quit`, `help`, `train`), and formats the output.
    *   **User Identity**: Parses `--user` CLI argument to support multiple user profiles.

### 2. `core/chatbot.py` (The Brain)
*   **Role**: The central logic controller.
*   **Logic Flow**:
    1.  Receives `user_input`.
    2.  **Check Cache**: First checks if this exact query has a cached response.
    3.  **Multi-Intent Split**: Splits input on punctuation (`.`, `?`, `!`, `;`).
    4.  **Check Local (Per Segment)**: If multiple segments exist, tries to match each locally and combine responses.
    5.  **Check Local (Full String)**: If no multi-intent match, tries matching the whole input.
    6.  **Check API**: If no local match is found, forwards the request to the `GeminiClient` with user context.
    7.  **Memory Extraction**: Parses AI response for user facts (e.g., "My name is X") and saves to profile.
    8.  **Smart Caching**: Only caches successful responses, not errors.
    9.  **History Management**: Appends exchanges to history for conversational context.

### 3. `core/intent_splitter.py` (The Segmenter)
*   **Role**: Splits user input into logical segments for multi-intent handling.
*   **Logic**: Uses regex to split on `.`, `?`, `!`, `;` and returns cleaned segments.

### 4. `core/user_manager.py` (The Memory Manager)
*   **Role**: Manages user-specific data persistence.
*   **Key Features**:
    *   Auto-detects OS username or uses `--user` override.
    *   Stores/loads profiles from `data/users/{username}.json`.
    *   Provides `get_context_string()` for AI context injection.
    *   Supports `set_fact()` and `get_fact()` for key-value storage.

### 5. `ai/gemini_client.py` (The Connector)
*   **Role**: Interfaces with Google's GenAI servers.
*   **Key Logic**:
    *   **Safe Import Handling**: Gracefully handles missing `google.genai` SDK.
    *   **Prompt Engineering**: Constructs the final payload sent to the AI.
        *   *System Instruction*: Prepended to every request: *"You are a helpful CLI assistant. Provide direct, concise answers..."*
        *   *Context*: Recent conversation history + User Profile facts.
    *   **Error Handling**: Catches network errors, 404s, Rate Limits, and returns safe fallback messages.
    *   **Response Extraction**: Uses `_extract_text()` to safely parse API responses.

### 6. `config.py` (The Control Panel)
*   **Role**: Centralized configuration using Python `dataclasses`.
*   **Settings**: Stores API keys, model names (`gemini-2.5-flash`), timeout settings, style preferences, auto-learning toggle, etc.

### 7. `local/pattern_matcher.py` (The Pattern Engine)
*   **Role**: Matches user input against local patterns and knowledge base.
*   **Features**:
    *   Regex pattern matching
    *   Fuzzy string matching (using `fuzzywuzzy`)
    *   Knowledge base search with tag-based lookup

### 8. `utils/cache.py` (The Cache Manager)
*   **Role**: LRU cache for responses with TTL expiration.
*   **Features**:
    *   Thread-safe operations using `threading.Lock`
    *   Automatic cache invalidation based on TTL
    *   Smart error filtering (doesn't cache error responses)

---

## 🔄 Enhanced Data Flow: Life of a Message

### Example: "Hello! What time is it?"

1.  **User types**: "Hello! What time is it?"
2.  **`main.py`** captures input and passes to `HybridChatbot`.
3.  **`HybridChatbot`** checks cache → No hit.
4.  **`IntentSplitter`** splits into: `["Hello", "What time is it"]`
5.  **Pattern Matching (Segment 1)**: "Hello" → matches `greetings` → "Hi there!"
6.  **Pattern Matching (Segment 2)**: "What time is it" → No local match.
7.  **Since not all segments matched locally**, falls back to single-string matching.
8.  **No full match**, forwards to **`GeminiClient`**.
9.  **`UserManager`** injects context: `"User Profile (muaza): name=Muaz"`
10. **`gemini_client`** constructs prompt with system instruction + user context + query.
11. **Google Gemini API** processes and returns response.
12. **`chatbot.py`** checks response for errors before caching.
13. **`chatbot.py`** extracts user facts (if any) from response via regex.
14. **`main.py`** receives the text, wraps it to terminal width, and prints.

---

## 🛡️ Reliability Features

*   **SDK Compatibility**: Gracefully handles missing or incompatible `google.genai` SDK with try/except blocks.
*   **Graceful Degradation**: If the internet cuts out or the API Key is invalid, the bot falls back to "Local Only" mode.
*   **UTF-8 Encoding**: All file operations use explicit `encoding='utf-8'` for cross-platform compatibility.
*   **Smart Regex Boundaries**: Auto-learned patterns correctly handle punctuation-ending queries.
*   **Thread-Safe Caching**: Response cache uses locks to prevent race conditions.
*   **Error Response Filtering**: Cache refuses to store error messages, ensuring retry capability.
*   **User Isolation**: Each user gets their own profile file for privacy and personalization.

---

## 🧠 Advanced Features

### Multi-Intent Handling
When you ask "Hi! How are you?", the bot:
1. Splits into `["Hi", "How are you"]`
2. Matches both locally (if patterns exist)
3. Combines: `"Hello! I'm doing great, thanks for asking!"`
4. Returns as `[LOCAL:multi]`

### Long-Term Memory
When you say "My name is Muaz":
1. AI responds: "Nice to meet you, Muaz!"
2. `chatbot.py` regex extracts: `name=Muaz`
3. Saves to `data/users/muaza.json`
4. Next session, AI receives: `"User Profile: name=Muaz"` in context

### Auto-Learning
When the AI gives a good response:
1. Checks for error keywords
2. If clean, saves as a new pattern in `patterns.json`
3. Future similar queries → instant local response (saves API quota)
