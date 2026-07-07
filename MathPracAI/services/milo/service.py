from llm.client import LLMConfigurationError, LLMProviderError, generate_text
from services.milo.models import MiloSession
from services.milo.prompt_builder import build_prompt
from services.milo.response_processor import build_tutor_response
from services.milo.runtime_builder import determine_runtime_state


class AITutorError(RuntimeError):
    pass


def create_tutor_response(student_message, context=None):
    session = MiloSession.from_request(student_message, context)
    if not session.student_message:
        raise ValueError("studentMessage is required.")
    session = session.with_runtime_state(determine_runtime_state(session))

    prompt, runtime_state = build_prompt(session)
    try:
        model_response = generate_text(prompt)
    except (LLMConfigurationError, LLMProviderError) as error:
        raise AITutorError(str(error)) from error

    return build_tutor_response(session, runtime_state, model_response, prompt)


def create_tutor_reply(student_message, context=None):
    return create_tutor_response(student_message, context).to_public_dict()
