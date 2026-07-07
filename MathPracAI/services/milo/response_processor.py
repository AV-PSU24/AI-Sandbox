from services.milo.models import AITutorResponse


DEFAULT_HELP_STATUS = "hint"


def build_tutor_response(session, runtime_state, model_response, assembled_prompt):
    return AITutorResponse(
        reply=model_response.text,
        help_status=response_help_status(session, runtime_state),
        diagnosis=None,
        suggested_actions=[],
        raw_model_response=model_response,
        assembled_prompt=assembled_prompt,
    )


def response_help_status(session, runtime_state):
    if session.help_status == "solution":
        return "solution"
    if runtime_state.value == "solution_explanation":
        return "solution"
    return DEFAULT_HELP_STATUS
