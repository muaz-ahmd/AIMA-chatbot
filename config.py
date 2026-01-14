import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class ChatbotConfig:
    """Comprehensive configuration for the chatbot"""
    
    # API Configuration
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY"))
    gemini_model: str = "gemini-2.5-flash"
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Local Pattern Matching
    pattern_match_threshold: float = 0.7
    use_fuzzy_matching: bool = True
    fuzzy_match_threshold: int = 80
    case_sensitive: bool = False
    
    # Response Configuration
    max_response_length: int = 2000
    response_temperature: float = 0.7
    enable_local_priority: bool = True
    fallback_to_ai: bool = True
    
    # Conversation Management
    max_history_length: int = 50
    context_window_size: int = 10
    enable_context: bool = True
    clear_history_on_restart: bool = False
    
    # Performance & Caching
    enable_response_cache: bool = True
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    
    # Input Processing
    min_input_length: int = 1
    max_input_length: int = 1000
    strip_whitespace: bool = True
    remove_special_chars: bool = False
    convert_to_lowercase: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/chatbot.log"
    log_conversations: bool = True
    
    # Data Persistence
    save_conversations: bool = True
    conversation_file: str = "data/conversation_history.json"
    save_user_preferences: bool = True
    preferences_file: str = "data/user_preferences.json"
    
    # UI/UX
    show_response_source: bool = True
    show_typing_indicator: bool = True
    typing_delay: float = 0.5
    enable_colors: bool = True
    prompt_symbol: str = "You: "
    bot_symbol: str = "Bot: "
    
    # Security
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    block_inappropriate_content: bool = True
    sanitize_input: bool = True
    
    # Advanced Features
    enable_sentiment_analysis: bool = False
    enable_intent_classification: bool = True
    enable_entity_extraction: bool = False
    multi_language_support: bool = False
    supported_languages: List[str] = field(default_factory=lambda: ["en"])
    
    # Error Handling
    graceful_degradation: bool = True
    default_error_response: str = "I'm sorry, I couldn't process that. Could you rephrase?"
    verbose_errors: bool = False
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    patterns_file: str = "local/patterns.json"
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        assert 0 <= self.pattern_match_threshold <= 1, "Threshold must be 0-1"
        assert 0 <= self.response_temperature <= 2, "Temperature must be 0-2"
        assert self.max_history_length > 0, "History length must be positive"
        assert self.cache_ttl_seconds > 0, "Cache TTL must be positive"
        return True
