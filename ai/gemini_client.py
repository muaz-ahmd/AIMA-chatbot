from typing import Optional, List
import time
import importlib
import logging
import importlib
import logging
try:
    from google import genai
except ImportError:
    genai = None

from config import ChatbotConfig


class GeminiClient:
    """Gemini API client with compatibility for `google.genai` and legacy `google.generativeai`.

    This client attempts to use the new `google.genai` package but will fall back
    to the older `google.generativeai` API if available.
    """

    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.model = None
        self.api = None
        self.initialized = False
        self.request_count = 0
        self.last_request_time = time.time()


    def initialize(self, api_key: str) -> bool:
        try:
            self.client = genai.Client(api_key=api_key)
            self.initialized = True
            return True
        except Exception as e:
            print(f"Gemini initialization error: {e}")
            return False


    def generate_response(self, prompt: str, context=None, temperature=None) -> str:
        if not self.initialized:
            return "AI service not initialized"

        if not self._check_rate_limit():
            return "Rate limit exceeded. Please wait."

        full_prompt = self._build_prompt(prompt, context)

        try:
            response = self.client.models.generate_content(
                model=self.config.gemini_model,  # e.g. "gemini-1.5-flash"
                contents=full_prompt
            )
            return self._extract_text(response)
        except Exception as e:
            err_msg = str(e).lower()
            # Handle common API errors with friendly messages
            if "429" in err_msg or "resource exhausted" in err_msg:
                return "⚠️ [API Limit] You're sending requests too fast or have hit your daily quota. Please wait."
            
            if "503" in err_msg or "unavailable" in err_msg or "overloaded" in err_msg:
                return "⚠️ [Server Busy] Google's AI service is overloaded right now. Please try again in a minute."
            
            if "404" in err_msg or "not found" in err_msg:
                return f"⚠️ [Config Error] The model '{self.config.gemini_model}' was not found. Please check your configuration."

            logging.getLogger('AmmaarBhaiChatBot').error(f"GenAI generation failed: {e}")
            return self.config.default_error_response


    def _extract_text(self, resp) -> str:
        """Attempt to extract text from various response shapes."""
        # direct text
        if resp is None:
            return ""
        if isinstance(resp, str):
            return resp
        # common attribute for legacy
        if hasattr(resp, 'text'):
            return getattr(resp, 'text')
        # new-style: outputs or output
        if hasattr(resp, 'outputs'):
            outs = getattr(resp, 'outputs')
            try:
                # outputs[0].content[0].text or outputs[0].text
                first = outs[0]
                if hasattr(first, 'content'):
                    content = first.content
                    if isinstance(content, list) and len(content) and hasattr(content[0], 'text'):
                        return content[0].text
                if hasattr(first, 'text'):
                    return first.text
            except Exception:
                pass
        if hasattr(resp, 'output'):
            outs = getattr(resp, 'output')
            try:
                first = outs[0]
                if isinstance(first, dict) and 'content' in first:
                    content = first['content']
                    if isinstance(content, list) and len(content) and 'text' in content[0]:
                        return content[0]['text']
            except Exception:
                pass
        # dict-like
        try:
            if isinstance(resp, dict):
                if 'text' in resp:
                    return resp['text']
                if 'outputs' in resp:
                    outs = resp['outputs']
                    if isinstance(outs, list) and len(outs):
                        o0 = outs[0]
                        if isinstance(o0, dict) and 'text' in o0:
                            return o0['text']
        except Exception:
            pass

        # fallback to string representation
        try:
            return str(resp)
        except Exception:
            return ''

    def _build_prompt(self, prompt: str, context: Optional[List[str]]) -> str:
        """Build prompt with context"""
        system_part = f"System: {self.config.system_instruction}\n\n"
        
        if not context or not self.config.enable_context:
            return f"{system_part}User: {prompt}"

        context_str = "\n".join(context[-self.config.context_window_size:])
        return f"{system_part}Context:\n{context_str}\n\nUser: {prompt}"

    def _check_rate_limit(self) -> bool:
        """Check rate limiting"""
        if not self.config.rate_limit_enabled:
            return True

        current_time = time.time()
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time

        if self.request_count >= self.config.max_requests_per_minute:
            return False

        self.request_count += 1
        return True
