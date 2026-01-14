from typing import Optional, List
import time
import importlib
import logging

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
        """Initialize Gemini/GenAI client using the available library."""
        try:
            # Prefer the new package
            try:
                genai = importlib.import_module('google.genai')
            except Exception:
                genai = importlib.import_module('google.generativeai')

            self.api = genai

            # Configure API key if supported
            if hasattr(genai, 'configure'):
                genai.configure(api_key=api_key)

            # Create model object (attempt modern and legacy constructors)
            if hasattr(genai, 'Model') and hasattr(genai.Model, 'from_pretrained'):
                # new google.genai style
                self.model = genai.Model.from_pretrained(self.config.gemini_model)
            elif hasattr(genai, 'GenerativeModel'):
                # legacy google.generativeai style
                self.model = genai.GenerativeModel(self.config.gemini_model)
            else:
                # last resort: store api as model and rely on module-level generate
                self.model = genai

            self.initialized = True
            return True
        except Exception as e:
            print(f"Gemini initialization error: {e}")
            return False

    def generate_response(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using the available GenAI client."""
        if not self.initialized:
            return "AI service not initialized"

        # Rate limiting
        if not self._check_rate_limit():
            return "Rate limit exceeded. Please wait."

        full_prompt = self._build_prompt(prompt, context)

        # Try multiple generation APIs for compatibility
        logger = logging.getLogger('AmmaarBhaiChatBot')
        last_error = None
        for attempt in range(max(1, self.config.max_retries)):
            try:
                # Legacy: model.generate_content(prompt, generation_config=genai.types.GenerationConfig(...))
                if hasattr(self.model, 'generate_content'):
                    genai = self.api
                    gen_cfg = None
                    if hasattr(genai, 'types') and hasattr(genai.types, 'GenerationConfig'):
                        gen_cfg = genai.types.GenerationConfig(
                            temperature=temperature or self.config.response_temperature,
                            max_output_tokens=self.config.max_response_length
                        )
                    resp = self.model.generate_content(full_prompt, generation_config=gen_cfg)
                    return self._extract_text(resp)

                # New: model.generate(input=..., temperature=..., max_output_tokens=...)
                if hasattr(self.model, 'generate'):
                    resp = self.model.generate(
                        input=full_prompt,
                        temperature=temperature or self.config.response_temperature,
                        max_output_tokens=self.config.max_response_length
                    )
                    return self._extract_text(resp)

                # Some clients expose `predict` or `predict_text` for text generation
                if hasattr(self.model, 'predict'):
                    resp = self.model.predict(full_prompt)
                    return self._extract_text(resp)
                if hasattr(self.model, 'predict_text'):
                    resp = self.model.predict_text(full_prompt)
                    return self._extract_text(resp)
                if hasattr(self.model, 'generate_text'):
                    resp = self.model.generate_text(full_prompt)
                    return self._extract_text(resp)

                # Module-level generate (last resort)
                if hasattr(self.api, 'generate'):
                    resp = self.api.generate(
                        model=self.config.gemini_model,
                        input=full_prompt,
                        temperature=temperature or self.config.response_temperature,
                        max_output_tokens=self.config.max_response_length
                    )
                    return self._extract_text(resp)

                # If none available, raise
                raise RuntimeError('No supported generate interface available on GenAI client')

            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    # Log the exception details for debugging
                    logger.exception("GenAI generation failed")
                    if self.config.verbose_errors:
                        return f"Error: {str(e)}"
                    return self.config.default_error_response

        if last_error:
            logger.warning("No generation interface succeeded; returning default error response")
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
        if not context or not self.config.enable_context:
            return prompt

        context_str = "\n".join(context[-self.config.context_window_size:])
        return f"Context:\n{context_str}\n\nUser: {prompt}"

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
