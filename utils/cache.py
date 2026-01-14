import time
from typing import Optional, Dict, Any
from collections import OrderedDict

from config import ChatbotConfig


class ResponseCache:
    """LRU cache for responses"""
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    
    def get(self, key: str) -> Optional[str]:
        """Get cached response"""
        if not self.config.enable_response_cache:
            return None
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() - entry['timestamp'] > self.config.cache_ttl_seconds:
                del self.cache[key]
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            return entry['value']
        
        return None
    
    def set(self, key: str, value: str):
        """Cache a response"""
        if not self.config.enable_response_cache:
            return
        
        # Remove oldest if at capacity
        if len(self.cache) >= self.config.cache_max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
