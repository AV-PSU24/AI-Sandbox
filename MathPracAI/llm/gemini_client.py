import os
import time

from config.env import load_environment
from llm.client import (
    DEFAULT_GEMINI_MODEL,
    LLMConfigurationError,
    LLMProviderError,
    LLMResponse,
    PROVIDER_GEMINI,
)


class GeminiLLMClient:
    def __init__(self, api_key=None, model=None):
        load_environment()
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY") or "").strip()
        self.model = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip()
        self.provider = PROVIDER_GEMINI
        self._client = None

        if not self.api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is required.")
        if not self.model:
            self.model = DEFAULT_GEMINI_MODEL

    def generate_text(self, prompt):
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("Prompt is required.")

        last_error = None
        for attempt in range(2):
            try:
                return self._generate_text_once(prompt)
            except Exception as error:
                if not is_retryable_provider_error(error) or attempt == 1:
                    raise
                last_error = error
                time.sleep(0.4)
        raise last_error

    def _generate_text_once(self, prompt):
        try:
            response = self._gemini_client().models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error

        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise LLMProviderError("Gemini returned an empty response.")
        return LLMResponse(text=text, model=self.model, provider=self.provider, raw_response=response)

    def _gemini_client(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError as error:
                raise LLMConfigurationError(
                    "google-genai is required. Install requirements.txt first."
                ) from error
            self._client = genai.Client(api_key=self.api_key)
        return self._client


def is_retryable_provider_error(error):
    text = str(error).lower()
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    return (
        status_code == 503
        or "503" in text
        or "unavailable" in text
        or "overloaded" in text
        or "try again later" in text
    )
