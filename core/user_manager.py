import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class UserManager:
    """Manages user identity and long-term memory."""
    
    def __init__(self, base_dir: Path, user_override: Optional[str] = None):
        self.base_dir = base_dir / "data" / "users"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine username
        if user_override:
            self.username = user_override
        else:
            try:
                self.username = os.getlogin()
            except Exception:
                self.username = "default_user"
                
        self.profile_file = self.base_dir / f"{self.username}.json"
        self.profile = self._load_profile()
        
    def _load_profile(self) -> Dict[str, Any]:
        """Load user profile from disk."""
        if self.profile_file.exists():
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.getLogger('AmmaarBhaiChatBot').error(f"Failed to load profile for {self.username}: {e}")
                
        # Default profile
        return {
            "username": self.username,
            "created_at": None,
            "facts": {},
            "preferences": {}
        }
    
    def save_profile(self):
        """Save user profile to disk."""
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            logging.getLogger('AmmaarBhaiChatBot').error(f"Failed to save profile: {e}")

    def get_fact(self, key: str) -> Optional[str]:
        return self.profile["facts"].get(key)
    
    def set_fact(self, key: str, value: str):
        self.profile["facts"][key] = value
        self.save_profile()
        
    def get_context_string(self) -> str:
        """Return a string summary of the user for AI context."""
        facts = self.profile.get("facts", {})
        if not facts:
            return ""
            
        summary = f"User Profile ({self.username}):\n"
        for k, v in facts.items():
            summary += f"- {k}: {v}\n"
        return summary
