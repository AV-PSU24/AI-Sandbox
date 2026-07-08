from dataclasses import dataclass, field

from math_engine.generators import evaluate_polynomial


UNAVAILABLE_PROBLEM_MESSAGE = "No problems available for the selected options."


@dataclass(frozen=True)
class ProblemContractResult:
    valid: bool
    reason: str = ""
    topic: str = ""
    failed_check: str = ""
    details: dict = field(default_factory=dict)


def valid_result(topic, details=None):
    return ProblemContractResult(
        valid=True,
        reason="Problem matches the selected generation contract.",
        topic=topic,
        details=details or {},
    )


def invalid_result(topic, failed_check, reason, details=None):
    return ProblemContractResult(
        valid=False,
        reason=reason,
        topic=topic,
        failed_check=failed_check,
        details=details or {},
    )


def selected_values(options, key):
    config = options.get("topic_config") if isinstance(options.get("topic_config"), dict) else {}
    raw_values = config.get(key)
    if isinstance(raw_values, str):
        return (raw_values,)
    if raw_values:
        return tuple(raw_values)
    return ()


def selected_views(options):
    raw_selected_views = options.get("selectedQuestionViews")
    if isinstance(raw_selected_views, str):
        return (raw_selected_views,)
    if raw_selected_views:
        return tuple(raw_selected_views)

    raw_views = options.get("questionViews")
    if isinstance(raw_views, str):
        return (raw_views,)
    if raw_views:
        return tuple(raw_views)
    return ()


def validate_problem_contract(problem, selected_topic, options=None, active_view=None):
    options = options if isinstance(options, dict) else {}
    shared = validate_shared_contract(problem, selected_topic, options, active_view)
    if not shared.valid:
        return shared

    validator = TOPIC_VALIDATORS.get(selected_topic)
    if validator is None:
        return valid_result(selected_topic)
    return validator(problem, selected_topic, options, active_view)


def validate_shared_contract(problem, selected_topic, options, active_view):
    if problem is None:
        return invalid_result(
            selected_topic,
            "problem_exists",
            "Generator did not return a problem object.",
        )
    if problem.topic != selected_topic:
        return invalid_result(
            selected_topic,
            "topic_matches_selection",
            "Generated problem topic does not match the selected topic.",
            {"problem_topic": problem.topic, "selected_topic": selected_topic},
        )
    if active_view == "equation" and not (problem.display_equation or problem.prompt or problem.assets):
        return invalid_result(
            selected_topic,
            "requested_representation_exists",
            "Equation/text view was requested but no visible text representation exists.",
        )
    if active_view == "graph" and not (
        isinstance(problem.graph_config, dict) and problem.graph_config.get("enabled")
    ):
        return invalid_result(
            selected_topic,
            "requested_representation_exists",
            "Graph view was requested but no graph representation exists.",
        )
    if not str(problem.answer or "").strip():
        return invalid_result(
            selected_topic,
            "answer_exists",
            "Generated problem does not contain an official answer.",
        )
    if not problem.acceptable_answers:
        return invalid_result(
            selected_topic,
            "acceptable_answers_exist",
            "Generated problem does not contain acceptable answers.",
        )
    if problem.answer_fields:
        for field in problem.answer_fields:
            if not str(field.get("correct_answer", problem.answer) or "").strip():
                return invalid_result(
                    selected_topic,
                    "answer_field_exists",
                    "Generated problem contains an empty answer field.",
                    {"field": field.get("name", "")},
                )
    return valid_result(selected_topic)


def validate_evaluating_functions(problem, selected_topic, options, active_view):
    metadata = problem.metadata if isinstance(problem.metadata, dict) else {}
    selected_families = selected_values(options, "functionFamilies")
    family = metadata.get("family")
    if selected_families and family not in selected_families:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated function family does not match selected function family options.",
            {"selected_families": selected_families, "family": family},
        )

    coefficients = metadata.get("coefficients")
    input_value = metadata.get("input_value")
    if not isinstance(coefficients, list) or input_value is None:
        return invalid_result(
            selected_topic,
            "metadata_supports_answer",
            "Evaluating-functions metadata is missing coefficients or input value.",
        )

    expected_answer = evaluate_polynomial(coefficients, input_value)
    if str(problem.answer) != str(expected_answer):
        return invalid_result(
            selected_topic,
            "answer_matches_actual_problem",
            "Official answer does not match the generated function and input.",
            {"expected_answer": expected_answer, "actual_answer": problem.answer},
        )

    if str(input_value) not in problem.prompt:
        return invalid_result(
            selected_topic,
            "visible_representation_supports_answer",
            "Visible prompt does not show the evaluation input.",
            {"input_value": input_value, "prompt": problem.prompt},
        )
    return valid_result(selected_topic)


def validate_domain_range(problem, selected_topic, options, active_view):
    metadata = problem.metadata if isinstance(problem.metadata, dict) else {}
    function_data = metadata.get("function") if isinstance(metadata.get("function"), dict) else {}
    selected_families = selected_values(options, "functionFamilies")
    selected_styles = selected_values(options, "functionStyles")
    selected_restrictions = selected_values(options, "domainRestrictions")
    requested_views = selected_views(options)

    family = function_data.get("family")
    function_style = metadata.get("function_style")
    restriction = metadata.get("domain_restriction")
    restriction_category = domain_range_restriction_category(metadata)
    presentation = metadata.get("presentation")
    if selected_families and family not in selected_families:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated function family does not match selected function family options.",
            {"selected_families": selected_families, "family": family},
        )
    if selected_styles and function_style not in selected_styles:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated function style does not match selected function style options.",
            {"selected_styles": selected_styles, "function_style": function_style},
        )
    if selected_restrictions and restriction_category not in selected_restrictions:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated domain/range restriction category does not match selected restriction options.",
            {
                "selected_restrictions": selected_restrictions,
                "domain_restriction": restriction,
                "restriction_category": restriction_category,
                "domain": metadata.get("domain"),
                "range": metadata.get("range"),
            },
        )
    if requested_views and presentation not in requested_views:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated presentation does not match selected question view options.",
            {"requested_views": requested_views, "presentation": presentation},
        )
    if active_view and presentation != active_view:
        return invalid_result(
            selected_topic,
            "selected_options_reflected",
            "Generated presentation does not match the active question view.",
            {"active_view": active_view, "presentation": presentation},
        )

    domain_segments = metadata.get("domain_segments") or []
    if restriction in ("restricted_interval", "union_of_intervals"):
        if not domain_segments:
            return invalid_result(
                selected_topic,
                "metadata_supports_answer",
                "Restricted domain/range problem is missing domain segments.",
            )
        if "equation" in requested_views and active_view != "equation":
            return invalid_result(
                selected_topic,
                "impossible_selected_combination",
                "Equation view is selected for a graph-only domain restriction.",
                {
                    "requested_views": requested_views,
                    "active_view": active_view,
                    "domain_restriction": restriction,
                },
            )
        if active_view == "equation" and not equation_view_shows_restriction(problem):
            return invalid_result(
                selected_topic,
                "visible_representation_supports_answer",
                "Equation view cannot support restricted-domain answers unless the restriction is visible.",
                {
                    "display_equation": problem.display_equation,
                    "prompt": problem.prompt,
                    "domain_restriction": restriction,
                    "domain_segments": domain_segments,
                },
            )
        if active_view == "graph":
            features = (
                problem.graph_config.get("features", {})
                if isinstance(problem.graph_config, dict)
                else {}
            )
            if not isinstance(features, dict) or not features.get("domain_segments"):
                return invalid_result(
                    selected_topic,
                    "visible_representation_supports_answer",
                    "Graph view cannot support restricted-domain answers without graph domain segments.",
                )

    if restriction == "none" and domain_segments:
        return invalid_result(
            selected_topic,
            "metadata_supports_answer",
            "Unrestricted domain/range problem should not contain restriction segments.",
        )
    return valid_result(selected_topic)


def domain_range_restriction_category(metadata):
    domain_value = str(metadata.get("domain", ""))
    range_value = str(metadata.get("range", ""))
    if "∪" in domain_value or "∪" in range_value:
        return "union_of_intervals"
    if domain_value != "(-∞, ∞)" or range_value != "(-∞, ∞)":
        return "restricted_interval"
    return "none"


def equation_view_shows_restriction(problem):
    visible_text = f"{problem.display_equation}\n{problem.prompt}"
    return any(marker in visible_text for marker in ("Domain:", "domain is", "restricted to", "≤ x ≤", "x ∈", "\\in"))


TOPIC_VALIDATORS = {
    "evaluating_functions": validate_evaluating_functions,
    "domain_and_range": validate_domain_range,
}
