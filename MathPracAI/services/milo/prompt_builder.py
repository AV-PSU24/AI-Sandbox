import os
from pathlib import Path

from services.milo.context_builder import build_context_components
from services.milo.models import PromptComponent
from services.milo.runtime_builder import build_runtime_prompt


ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = ROOT / "prompts" / "milo"
SYSTEM_PROMPT_PATH = PROMPT_ROOT / "system.txt"
ACTION_PROMPT_PATHS = {
    "hint": PROMPT_ROOT / "actions" / "hint.txt",
    "solution": PROMPT_ROOT / "actions" / "solution.txt",
}
DEFAULT_DEBUG_PROMPT_PATH = ROOT / "debug" / "latest_prompt.txt"


def build_prompt(session):
    runtime_state, runtime_prompt = build_runtime_prompt(session)
    components = [
        PromptComponent("System Prompt", _read_prompt_file(SYSTEM_PROMPT_PATH)),
        PromptComponent("Runtime Prompt", runtime_prompt),
        *build_action_components(session),
        *build_context_components(session),
    ]
    prompt = assemble_prompt(components)
    maybe_write_debug_prompt(prompt)
    return prompt, runtime_state


def assemble_prompt(components):
    sections = []
    for component in components:
        content = component.content.strip()
        if content:
            if content.startswith("========================="):
                sections.append(content)
            else:
                sections.append(f"{section_title(component.name)}\n{content}")
    return "\n\n".join(sections)


def maybe_write_debug_prompt(prompt):
    if os.environ.get("MILO_PROMPT_DEBUG", "").strip().lower() not in ("1", "true", "yes"):
        return
    debug_path = Path(os.environ.get("MILO_PROMPT_DEBUG_PATH") or DEFAULT_DEBUG_PROMPT_PATH)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(prompt, encoding="utf-8")


def _read_prompt_file(path):
    return path.read_text(encoding="utf-8").strip()


def section_title(title):
    return f"=========================\n{title.upper()}\n========================="


def build_action_components(session):
    prompt_path = ACTION_PROMPT_PATHS.get(session.action_mode)
    if not prompt_path:
        return []
    return [PromptComponent("Action Prompt", _read_prompt_file(prompt_path))]
