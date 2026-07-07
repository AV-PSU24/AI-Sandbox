import json
from pathlib import Path

from llm.llm_client import LLMConfigurationError, LLMProviderError, generate_text


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_PATH = ROOT / "prompts" / "ai_tutor" / "system.txt"
DEFAULT_HELP_STATUS = "hint"


class AITutorError(RuntimeError):
    pass


def create_tutor_reply(student_message, context=None):
    message = (student_message or "").strip()
    if not message:
        raise ValueError("studentMessage is required.")

    prompt = build_tutor_prompt(message, context or {})
    try:
        response = generate_text(prompt)
    except (LLMConfigurationError, LLMProviderError) as error:
        raise AITutorError(str(error)) from error

    return {
        "ok": True,
        "reply": response.text,
        "helpStatus": DEFAULT_HELP_STATUS,
        "diagnosis": None,
        "suggestedActions": [],
    }


def build_tutor_prompt(student_message, context):
    sections = [
        read_system_prompt(),
        "Student message:",
        student_message,
    ]
    compact_context = compact_future_context(context)
    if compact_context:
        sections.extend(["Context:", compact_context])
    return "\n\n".join(sections)


def read_system_prompt():
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def compact_future_context(context):
    allowed_keys = (
        "unit",
        "topic",
        "problem",
        "attempts",
        "chatHistory",
        "attemptCount",
        "solutionUnlocked",
        "helpStatus",
    )
    compact = {key: context.get(key) for key in allowed_keys if key in context}
    if not compact:
        return ""
    return json.dumps(compact, ensure_ascii=True, sort_keys=True)
