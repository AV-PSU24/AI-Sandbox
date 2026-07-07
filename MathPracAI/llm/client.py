import os
from dataclasses import dataclass

from config.env import load_environment


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
PROVIDER_GEMINI = "gemini"


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    raw_response: object = None


def llm_environment_status():
    load_environment()
    return {
        "provider": PROVIDER_GEMINI,
        "api_key_detected": bool((os.environ.get("GEMINI_API_KEY") or "").strip()),
        "model": (os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip(),
    }


def create_llm_client():
    from llm.gemini_client import GeminiLLMClient

    return GeminiLLMClient()


def generate_text(prompt):
    return create_llm_client().generate_text(prompt)
