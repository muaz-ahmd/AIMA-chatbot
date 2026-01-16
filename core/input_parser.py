import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from config import ChatbotConfig

@dataclass
class ParsedInput:
    """Structured representation of parsed input"""
    raw_text: str
    normalized_text: str
    tokens: List[str]
    intent: Optional[str] = None
    entities: Dict[str, str] = field(default_factory=dict)
    sentiment: Optional[str] = None
    confidence: float = 0.0


class InputParser:
    """Advanced input parsing and normalization"""
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        # Comprehensive stop words list
        self.stop_words = {
            # Articles
            'a', 'an', 'the',
            # Common verbs (be careful with these in questions)
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'do', 'does', 'did', 'doing',
            'have', 'has', 'had', 'having',
            # Pronouns
            'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'hers', 'its', 'our', 'their',
            # Prepositions
            'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below',
            # Conjunctions
            'and', 'but', 'or', 'so', 'yet', 'nor', 'though',
            # Other common words
            'this', 'that', 'these', 'those',
            'can', 'could', 'will', 'would', 'should',
            'may', 'might', 'must',
            # Additional common filler (PURE filler only)
            'please', 'just', 'really', 'very'
        }
    
    def parse(self, user_input: str) -> ParsedInput:
        """Parse and analyze user input"""
        raw = user_input
        
        # Normalize
        normalized = self._normalize(user_input)
        
        # Tokenize
        tokens = self._tokenize(normalized)
        
        return ParsedInput(
            raw_text=raw,
            normalized_text=normalized,
            tokens=tokens
        )
    
    def _normalize(self, text: str) -> str:
        """Normalize input text"""
        if self.config.strip_whitespace:
            text = text.strip()
        
        if self.config.convert_to_lowercase:
            text = text.lower()
        
        if self.config.remove_special_chars:
            text = re.sub(r'[^\w\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """Split text into tokens"""
        return text.split()
    
    def validate_input(self, text: str) -> Tuple[bool, str]:
        """Validate user input"""
        if not text or len(text) < self.config.min_input_length:
            return False, "Input too short"
        
        if len(text) > self.config.max_input_length:
            return False, "Input too long"
        
        if self.config.sanitize_input:
            # Check for potentially harmful patterns
            dangerous_patterns = [r'<script', r'javascript:', r'onerror=']
            for pattern in dangerous_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, "Invalid input detected"
        
        return True, "Valid"
    
    def normalize_for_pattern(self, text: str) -> str:
        """Normalize text for pattern matching/storage by removing stop words and special chars"""
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Tokenize
        tokens = text.split()
        
        # Remove stop words while preserving order
        filtered_tokens = [t for t in tokens if t not in self.stop_words and len(t) > 1]
        
        # Join back
        normalized = ' '.join(filtered_tokens)
        
        return normalized if normalized else text.lower()  # Fallback to original if all words filtered
