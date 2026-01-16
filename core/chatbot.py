from typing import Optional, List, Dict
import time
from datetime import datetime

from config import ChatbotConfig
from core.input_parser import InputParser, ParsedInput
from core.intent_splitter import IntentSplitter
from core.user_manager import UserManager
from local.pattern_matcher import PatternMatcher
from ai.gemini_client import GeminiClient
from utils.logger import ChatbotLogger
from utils.cache import ResponseCache
from utils.math_solver import MathSolver


class HybridChatbot:
    """Main chatbot orchestrator"""
    
    def __init__(self, config: ChatbotConfig, user_override: Optional[str] = None):
        self.config = config
        self.parser = InputParser(config)
        self.splitter = IntentSplitter()
        self.user_manager = UserManager(config.base_dir, user_override)
        self.math_solver = MathSolver()
        self.pattern_matcher = PatternMatcher(
            config,
            config.patterns_file,
            parser=self.parser
        )
        self.gemini_client = GeminiClient(config)
        self.logger = ChatbotLogger(config)
        self.cache = ResponseCache(config)
        
        self.conversation_history = []
        self.session_start = datetime.now()
        self.stats = {
            'total_queries': 0,
            'local_responses': 0,
            'ai_responses': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    def initialize(self, api_key: Optional[str] = None) -> bool:
        """Initialize chatbot components"""
        self.logger.info("Initializing chatbot...")
        
        # Validate config
        try:
            self.config.validate()
        except AssertionError as e:
            self.logger.error(f"Config validation failed: {e}")
            return False
        
        # Initialize Gemini if API key provided
        if api_key:
            if self.gemini_client.initialize(api_key):
                self.logger.info("Gemini API initialized")
            else:
                self.logger.warning("Gemini API initialization failed")
                if not self.config.graceful_degradation:
                    return False
        
        # Load conversation history
        if self.config.save_conversations and not self.config.clear_history_on_restart:
            self._load_history()
            
        self.logger.info(f"Chatbot initialized for user: {self.user_manager.username}")
        return True
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response"""
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        try:
            # Validate input
            is_valid, message = self.parser.validate_input(user_input)
            if not is_valid:
                self.logger.warning(f"Invalid input: {message}")
                return f"Invalid input: {message}"
            
            # Parse input
            parsed = self.parser.parse(user_input)
            self.logger.debug(f"Parsed input: {parsed.normalized_text}")
            
            # Check cache
            if self.config.enable_response_cache:
                cached = self.cache.get(parsed.normalized_text)
                if cached:
                    self.stats['cache_hits'] += 1
                    self.logger.debug("Cache hit")
                    return self._format_response(cached, "CACHED")
            
            # Check if input is a math expression (try extraction first, then direct)
            expression_to_solve = None
            
            # First, try to extract expression from natural language
            extracted = self.math_solver.extract_expression(user_input)
            if extracted:
                expression_to_solve = extracted
            # If no extraction, check if the entire input is a direct math expression
            elif self.math_solver.is_math_expression(user_input):
                expression_to_solve = user_input
            
            # If we have an expression, solve it
            if expression_to_solve:
                result = self.math_solver.solve(expression_to_solve)
                if result:
                    value, formatted = result
                    response = f"{expression_to_solve} = {formatted}"
                    
                    # Cache math result
                    if self.config.enable_response_cache:
                        self.cache.set(parsed.normalized_text, response)
                    
                    # Add to history
                    self._add_to_history(user_input, response, "MATH")
                    self.stats['local_responses'] += 1
                    
                    self.logger.info(f"Math calculation: {response}")
                    return self._format_response(response, "MATH")
            
            # Try local pattern matching first (Standard)
            if self.config.enable_local_priority:
                # 1. Try Multi-Intent Split first
                # Check if we can answer ALL segments locally.
                segments = self.splitter.split(user_input)
                if len(segments) > 1:
                    combined_responses = []
                    all_segments_matched = True
                    
                    for seg in segments:
                        # We need to parse each segment individually for the matcher
                        seg_parsed = self.parser.parse(seg)
                        match_result = self.pattern_matcher.match(seg_parsed)
                        
                        if match_result.matched and match_result.confidence >= self.config.pattern_match_threshold:
                            combined_responses.append(match_result.response)
                        else:
                            all_segments_matched = False
                            break
                    
                    if all_segments_matched and combined_responses:
                        final_response = " ".join(combined_responses)
                        self.stats['local_responses'] += 1
                        self._add_to_history(user_input, final_response, "LOCAL")
                        self.logger.info(f"Multi-intent local match: {len(segments)} segments")
                        return self._format_response(final_response, "LOCAL", "multi")

                # 2. Try Standard Full Match
                match_result = self.pattern_matcher.match(parsed)
                
                if match_result.matched and match_result.confidence >= self.config.pattern_match_threshold:
                    self.stats['local_responses'] += 1
                    response = match_result.response
                    
                    # Cache response (local responses are safe to cache)
                    if self.config.enable_response_cache:
                        self.cache.set(parsed.normalized_text, response)
                    
                    # Log conversation
                    self._add_to_history(user_input, response, "LOCAL")
                    
                    self.logger.info(f"Local match: {match_result.pattern_name} (confidence: {match_result.confidence:.2f})")
                    return self._format_response(response, "LOCAL", match_result.match_type)
            
            # Fallback to AI
            if self.config.fallback_to_ai and self.gemini_client.initialized:
                self.stats['ai_responses'] += 1
                
                # Get context if enabled
                context = None
                if self.config.enable_context:
                    context = self._get_context()
                    
                # Inject User Profile Context
                user_context = self.user_manager.get_context_string()
                if user_context:
                    # We can prepend this to the prompt or the system instruction. 
                    # Prepending to system instruction via prompt is cleaner if client supports it,
                    # but here we pass context as list. Let's prepend to the prompt input for now.
                    # Or better: Add it to the context list as a system note.
                    if context is None:
                        context = []
                    context.append(f"System Note: {user_context}")

                response = self.gemini_client.generate_response(
                    user_input,
                    context=context
                )
                
                # Cache response (only if not an error)
                if self.config.enable_response_cache:
                    # Don't cache error responses
                    error_keywords = [
                        "error", "sorry", "unable", "cannot", "failed", "404", "503",
                        "api limit", "server busy", "config error", "quota", "resource exhausted"
                    ]
                    is_error = any(k in response.lower() for k in error_keywords)
                    if not is_error:
                        self.cache.set(parsed.normalized_text, response)
                
                # Auto Learning
                if self.config.enable_auto_learning:
                    # Basic validation to avoid learning errors
                    error_keywords = [
                        "error", "sorry", "unable", "cannot", "failed", "404", "503",
                        "api limit", "server busy", "config error", "quota"
                    ]
                    is_error = any(k in response.lower() for k in error_keywords)
                    
                    if not is_error and len(response) > 5:
                         # normalize pattern for storage
                         self.learn_pattern(user_input, response)
                         self.logger.info("Auto-learned new pattern")

                # Simple User Fact Extraction (Basic Logic)
                import re
                # "My name is X"
                name_match = re.search(r"my name is\s+([a-zA-Z]+)", user_input, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1)
                    self.user_manager.set_fact("name", name)
                    self.logger.info(f"Learned user name: {name}")

                # Log conversation
                self._add_to_history(user_input, response, "GEMINI")
                
                self.logger.info("AI response generated")
                return self._format_response(response, "GEMINI")
            
            # No response available
            return self.config.default_error_response
        
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing input: {e}", exc_info=True)
            
            if self.config.verbose_errors:
                return f"Error: {str(e)}"
            return self.config.default_error_response
    
    def learn_pattern(self, pattern: str, response: str) -> bool:
        """Learn a new pattern and save to file with normalization and duplicate detection"""
        try:
            import json
            import os
            import re
            from fuzzywuzzy import fuzz
            
            # Normalize pattern for comparison
            normalized = self.parser.normalize_for_pattern(pattern.strip())
            
            if not normalized:
                self.logger.warning("Pattern normalized to empty string, skipping")
                return False
            
            # Load existing
            if os.path.exists(self.config.patterns_file):
                with open(self.config.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # Check for similar existing pattern
            similar_key = self._find_similar_pattern(normalized, data)
            
            if similar_key:
                # Update existing pattern instead of creating duplicate
                self.logger.info(f"Merging with similar pattern: {similar_key}")
                
                # Add response if not already present
                existing_responses = data[similar_key].get("responses", [])
                if response not in existing_responses:
                    existing_responses.append(response)
                    data[similar_key]["responses"] = existing_responses
                    
                    with open(self.config.patterns_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    self.pattern_matcher.load_patterns()
                    return True
                else:
                    self.logger.info("Response already exists for this pattern")
                    return False
            else:
                # Create new pattern with tags
                # Extract tags (keywords) from normalized pattern
                tags = normalized.split()
                
                # Create regex pattern that's more flexible
                # Use word boundaries for each tag
                tag_patterns = [re.escape(tag) for tag in tags]
                regex_pattern = r"\b" + r".*".join(tag_patterns) + r"\b"
                
                import uuid
                cat_id = f"learned_{uuid.uuid4().hex[:8]}"
                data[cat_id] = {
                    "patterns": [regex_pattern],
                    "responses": [response],
                    "tags": tags,  # Store tags for semantic matching
                    "normalized": normalized,  # Store normalized form
                    "original_query": pattern.strip(),  # Store original for reference
                    "priority": 9  # High priority for learned items
                }
                
                with open(self.config.patterns_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Reload matcher
                self.pattern_matcher.load_patterns()
                self.logger.info(f"Learned new pattern with tags: {tags}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to learn pattern: {e}")
            return False
    
    def _find_similar_pattern(self, normalized_pattern: str, patterns_data: dict, threshold: float = 0.85) -> Optional[str]:
        """Find if a similar pattern already exists using fuzzy matching"""
        from fuzzywuzzy import fuzz
        
        best_score = 0
        best_match = None
        
        for name, data in patterns_data.items():
            if name.startswith("learned_"):
                # Compare with normalized form if available
                existing_normalized = data.get("normalized", "")
                
                if existing_normalized:
                    # Token sort ratio is more robust for deduplication as it respects word count
                    score = fuzz.token_sort_ratio(normalized_pattern, existing_normalized) / 100.0
                    
                    if score >= 0.9 and score > best_score:
                        best_score = score
                        best_match = name
        
        return best_match if best_score >= 0.9 else None
    
    def _format_response(self, response: str, source: str, match_type: str = "") -> str:
        """Format response with source indicator"""
        if self.config.show_response_source:
            prefix = f"[{source}"
            if match_type:
                prefix += f":{match_type}"
            prefix += "] "
            return prefix + response
        return response
    
    def _add_to_history(self, user_input: str, response: str, source: str):
        """Add exchange to conversation history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'bot': response,
            'source': source
        }
        
        self.conversation_history.append(entry)
        
        # Trim history if needed
        if len(self.conversation_history) > self.config.max_history_length:
            self.conversation_history = self.conversation_history[-self.config.max_history_length:]
        
        # Save to file
        if self.config.save_conversations and self.config.log_conversations:
            self._save_history()
    
    def _get_context(self) -> List[str]:
        """Get recent conversation context"""
        context = []
        recent = self.conversation_history[-self.config.context_window_size:]
        
        for entry in recent:
            context.append(f"User: {entry['user']}")
            context.append(f"Bot: {entry['bot']}")
        
        return context
    
    def _load_history(self):
        """Load conversation history from file"""
        try:
            import json
            with open(self.config.conversation_file, 'r') as f:
                self.conversation_history = json.load(f)
            self.logger.info(f"Loaded {len(self.conversation_history)} conversations")
        except FileNotFoundError:
            self.logger.info("No previous conversation history found")
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
    
    def _save_history(self):
        """Save conversation history to file"""
        try:
            import json
            import os
            
            os.makedirs(os.path.dirname(self.config.conversation_file), exist_ok=True)
            
            with open(self.config.conversation_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")
    
    def get_statistics(self) -> Dict:
        """Get chatbot statistics"""
        uptime = datetime.now() - self.session_start
        
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'cache_size': len(self.cache.cache),
            'history_length': len(self.conversation_history)
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        if self.config.save_conversations:
            self._save_history()
        self.logger.info("Conversation history cleared")
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down chatbot...")
        
        if self.config.save_conversations:
            self._save_history()
        
        stats = self.get_statistics()
        self.logger.info(f"Session stats: {stats}")
        self.logger.info("Chatbot shutdown complete")
