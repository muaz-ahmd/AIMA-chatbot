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
    
    def __init__(self, config: ChatbotConfig, patterns_file: str, parser=None):
        self.config = config
        self.patterns = self._load_patterns(patterns_file)
        self.knowledge_base = self._load_knowledge_base()
        self.match_cache = {}
        self.parser = parser

    def load_patterns(self):
        """Reload patterns from file"""
        self.patterns = self._load_patterns(self.config.patterns_file)
        self.knowledge_base = self._load_knowledge_base()
        self.match_cache = {}

    def _load_knowledge_base(self) -> List[Dict]:
        """Load knowledge base from JSON file"""
        try:
            if hasattr(self.config, 'knowledge_file'):
                with open(self.config.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"[ERROR] Failed to load knowledge base: {e}")
            return []

    def search_knowledge(self, text: str) -> Optional[str]:
        """Search knowledge base for a match"""
        if not self.knowledge_base or len(text) < 3:
            return None
            
        text = text.lower()
        threshold = getattr(self.config, 'min_knowledge_score', 85)
        
        best_score = 0
        best_content = None
        
        for entry in self.knowledge_base:
            # 1. Tags Match (Priority) - strict partial ratio
            # We want "VC" to match "Vice Chancellor" tag, but "Delhi University" shouldn't match "Delhi" tag easily
            for tag in entry.get("tags", []):
                # ratio is strict exactness, partial_ratio allows "subset"
                # For tags, we want high relevance.
                score = fuzz.ratio(tag.lower(), text)
                if score >= threshold:
                    return entry["content"] # Immediate return on high tag match
                
                # Check partial but with very high threshold
                p_score = fuzz.partial_ratio(tag.lower(), text)
                if p_score >= 95 and len(text) > 4: # Only for longer queries
                     if p_score > best_score:
                        best_score = p_score
                        best_content = entry["content"]

            # 2. Content Match (Wildcard)
            # Token Set Ratio: Matches if query words appear in content
            content_score = fuzz.token_set_ratio(entry["content"].lower(), text)
            
            # Penalize if query is "Delhi University" and content has "Delhi" but implies something else?
            # Hard to do without NLP.
            # Rely on high threshold (85).
            
            if content_score > best_score:
                best_score = content_score
                best_content = entry["content"]
        
        if best_score >= threshold:
            return best_content
        return None
    
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
        
        # Try standard patterns first
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
        
        # Try Knowledge Base Search (New Layer)
        kb_result = self.search_knowledge(text)
        if kb_result:
             result = MatchResult(
                matched=True,
                response=kb_result,
                pattern_name="knowledge_base",
                confidence=0.9,
                match_type="knowledge"
            )
             self.match_cache[text] = result
             return result

        # Try Tag-Based Semantic Matching (New)
        if self.parser:
            tag_result = self._tag_match(text)
            if tag_result.matched:
                self.match_cache[text] = tag_result
                return tag_result

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
                    
                    # Use lower threshold for learned patterns
                    threshold = self.config.fuzzy_match_threshold
                    if name.startswith("learned_"):
                        threshold = min(threshold, 60) # Lower for learned
                        
                    if score > best_score and score >= threshold:
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

    def _tag_match(self, text: str) -> MatchResult:
        """Match based on semantic tags rather than full text"""
        if not self.parser:
            return MatchResult(False, None, "", 0.0, "none")
            
        # Get tags from input
        input_normalized = self.parser.normalize_for_pattern(text)
        input_tags = set(input_normalized.split())
        
        if not input_tags:
            return MatchResult(False, None, "", 0.0, "none")
            
        best_score = 0
        best_match = None
        
        for name, data in self.patterns.items():
            # Get tags from pattern data
            pattern_tags = data.get("tags")
            if not pattern_tags:
                # Fallback: create tags from normalized if available
                norm = data.get("normalized")
                if norm:
                    pattern_tags = norm.split()
            
            if not pattern_tags:
                continue
                
            pattern_tags_set = set(pattern_tags)
            
            # Calculate Jaccard similarity (Intersection over Union)
            intersection = input_tags & pattern_tags_set
            union = input_tags | pattern_tags_set
            
            if not union:
                continue
                
            score = len(intersection) / len(union)
            
            # Weighted score: count matches relative to pattern tags
            # We want "linux distro" to match "linux distro best" well
            recall = len(intersection) / len(pattern_tags_set)
            
            # Combined score
            final_score = (score * 0.4) + (recall * 0.6)
            
            if final_score > best_score:
                best_score = final_score
                best_match = (name, data)
        
        # Dynamic threshold for semantic matching
        base_threshold = 0.7
        best_name = best_match[0] if best_match else ""
        if best_name.startswith("learned_"):
            base_threshold = 0.6 # Lower for learned
            
        if best_match and best_score >= base_threshold:
            return MatchResult(
                matched=True,
                response=self._select_response(best_match[1]["responses"]),
                pattern_name=best_match[0],
                confidence=best_score,
                match_type="semantic"
            )
            
        return MatchResult(False, None, "", 0.0, "none")
    
    def _select_response(self, responses: List[str]) -> str:
        """Select a response from available options"""
        import random
        if not responses:
            return "I don't have a response for this."
        return random.choice(responses)
