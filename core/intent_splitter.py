import re
from typing import List

class IntentSplitter:
    """Splits user input into separate logical segments."""
    
    def __init__(self):
        # Split on . ? ! ; and optionally newlines, attempting to respect common abbreviations if needed (simple ver first)
        self.split_pattern = r'[.?!;]+'

    def split(self, text: str) -> List[str]:
        """
        Split text into segments.
        Example: "Hello! How are you?" -> ["Hello", "How are you"]
        """
        if not text:
            return []
            
        # Split by punctuation
        # We use capturing group to keep delimiter if we wanted, but here we just want segments
        segments = re.split(self.split_pattern, text)
        
        # Clean up
        cleaned = [s.strip() for s in segments if s.strip()]
        
        return cleaned
