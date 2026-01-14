import re
import json
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

from fuzzywuzzy import fuzz

from config import ChatbotConfig
from core.input_parser import ParsedInput

@dataclass
class MatchResult:
    """Result of pattern matching"""
    matched: bool
    response: Optional[str]
    pattern_name: str
    confidence: float
    match_type: str  # 'exact', 'regex', 'fuzzy'


class PatternMatcher:
    """Advanced pattern matching engine"""
    
    def __init__(self, config: ChatbotConfig, patterns_file: str):
        self.config = config
        self.patterns = self._load_patterns(patterns_file)
        self.match_cache = {}
    
    def _load_patterns(self, filepath: str) -> Dict:
        """Load patterns from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict:
        """Default patterns if file doesn't exist"""
        return {
            "greetings": {
                "patterns": [
                    r"\b(hello|hi|hey|greetings|howdy)\b",
                    "good morning",
                    "good afternoon",
                    "good evening"
                ],
                "responses": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Hey! How's it going?"
                ],
                "priority": 10
            },
            "farewell": {
                "patterns": [
                    r"\b(bye|goodbye|see you|farewell|exit|quit)\b"
                ],
                "responses": [
                    "Goodbye! Have a great day!",
                    "See you later!",
                    "Take care!"
                ],
                "priority": 10
            },
            "gratitude": {
                "patterns": [
                    r"\b(thank|thanks|thx|appreciate)\b"
                ],
                "responses": [
                    "You're welcome!",
                    "Happy to help!",
                    "Anytime!"
                ],
                "priority": 8
            },
            "status": {
                "patterns": [
                    r"\b(how are you|how do you do|whats up)\b"
                ],
                "responses": [
                    "I'm doing great! How about you?",
                    "I'm here and ready to help!"
                ],
                "priority": 7
            }
        }
    
    def match(self, parsed_input: ParsedInput) -> MatchResult:
        """Match input against patterns"""
        text = parsed_input.normalized_text
        
        # Check cache first
        if text in self.match_cache:
            return self.match_cache[text]
        
        best_match = MatchResult(
            matched=False,
            response=None,
            pattern_name="",
            confidence=0.0,
            match_type="none"
        )
        
        # Try exact/regex matching first
        for name, data in self.patterns.items():
            for pattern in data.get("patterns", []):
                if self._is_regex_pattern(pattern):
                    if re.search(pattern, text, re.IGNORECASE):
                        result = MatchResult(
                            matched=True,
                            response=self._select_response(data["responses"]),
                            pattern_name=name,
                            confidence=1.0,
                            match_type="regex"
                        )
                        self.match_cache[text] = result
                        return result
                else:
                    if pattern.lower() in text:
                        result = MatchResult(
                            matched=True,
                            response=self._select_response(data["responses"]),
                            pattern_name=name,
                            confidence=1.0,
                            match_type="exact"
                        )
                        self.match_cache[text] = result
                        return result
        
        # Try fuzzy matching if enabled
        if self.config.use_fuzzy_matching:
            fuzzy_result = self._fuzzy_match(text)
            if fuzzy_result.matched:
                return fuzzy_result
        
        return best_match
    
    def _is_regex_pattern(self, pattern: str) -> bool:
        """Check if pattern is regex"""
        return any(c in pattern for c in r'\[](){}^$.*+?|')
    
    def _fuzzy_match(self, text: str) -> MatchResult:
        """Perform fuzzy matching"""
        best_score = 0
        best_match = None
        
        for name, data in self.patterns.items():
            for pattern in data.get("patterns", []):
                if not self._is_regex_pattern(pattern):
                    score = fuzz.partial_ratio(text, pattern.lower())
                    if score > best_score and score >= self.config.fuzzy_match_threshold:
                        best_score = score
                        best_match = (name, data)
        
        if best_match:
            return MatchResult(
                matched=True,
                response=self._select_response(best_match[1]["responses"]),
                pattern_name=best_match[0],
                confidence=best_score / 100.0,
                match_type="fuzzy"
            )
        
        return MatchResult(False, None, "", 0.0, "none")
    
    def _select_response(self, responses: List[str]) -> str:
        """Select a response from available options"""
        import random
        return random.choice(responses)
