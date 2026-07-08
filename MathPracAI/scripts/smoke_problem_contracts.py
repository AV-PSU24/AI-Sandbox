from itertools import combinations, product
from pathlib import Path
from random import seed
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from math_engine.problem_contracts import UNAVAILABLE_PROBLEM_MESSAGE, validate_problem_contract
from math_engine.generators import GENERATORS
from math_engine.renderers import (
    DEFAULT_QUESTION_VIEW_OPTIONS,
    QUESTION_VIEW_OPTIONS_BY_TOPIC,
    TOPIC_CONFIG_SECTIONS_BY_TOPIC,
)
from routes.practice_routes import generate_problem


def nonempty_subsets(values):
    values = tuple(values)
    for size in range(1, len(values) + 1):
        for selected in combinations(values, size):
            yield selected


def topic_matrix(topic):
    sections = TOPIC_CONFIG_SECTIONS_BY_TOPIC.get(topic, ())
    keys = [section["key"] for section in sections]
    option_groups = [
        tuple(nonempty_subsets(value for value, _label in section["options"]))
        for section in sections
    ]
    views = tuple(value for value, _label in QUESTION_VIEW_OPTIONS_BY_TOPIC.get(topic, DEFAULT_QUESTION_VIEW_OPTIONS))
    if not option_groups:
        option_groups = [()]

    for selected_groups in product(*option_groups):
        config = dict(zip(keys, selected_groups))
        for selected_views in nonempty_subsets(views):
            for active_view in selected_views:
                yield config, selected_views, active_view


def impossible_domain_range(config, selected_views):
    families = set(config.get("functionFamilies", ()))
    restrictions = set(config.get("domainRestrictions", ()))
    possible = set()
    if "equation" in selected_views:
        if families & {"linear", "cubic"}:
            possible.add("none")
        if families & {"quadratic", "absolute_value", "square_root"}:
            possible.add("restricted_interval")
    elif "graph" in selected_views:
        if families & {"linear", "cubic"}:
            possible.add("none")
        if families & {"quadratic", "absolute_value", "square_root"}:
            possible.add("restricted_interval")
        if restrictions & {"restricted_interval", "union_of_intervals"}:
            possible.update(restrictions & {"restricted_interval", "union_of_intervals"})
    return not bool(possible & restrictions)


def expected_unavailable(topic, config, selected_views):
    if topic == "domain_and_range":
        return impossible_domain_range(config, selected_views)
    return False


def problem_summary(problem):
    if problem is None:
        return {}
    metadata = problem.metadata or {}
    return {
        "equation": problem.display_equation,
        "answers": {field.get("name"): field.get("correct_answer") for field in problem.answer_fields or []},
        "metadata": {
            "presentation": metadata.get("presentation"),
            "family": metadata.get("family") or (metadata.get("function") or {}).get("family"),
            "function_style": metadata.get("function_style"),
            "domain_restriction": metadata.get("domain_restriction"),
        },
    }


def run_matrix():
    seed(7)
    topics = ("evaluating_functions", "domain_and_range")
    summary = {
        "valid": 0,
        "expected_unavailable": 0,
        "unexpected_unavailable": 0,
        "invalid": 0,
    }
    failures = []

    for topic in topics:
        for config, selected_views, active_view in topic_matrix(topic):
            state = {
                "topic": topic,
                "active_question_view": active_view,
                "question_view_equation": "true" if "equation" in selected_views else "",
                "question_view_graph": "true" if "graph" in selected_views else "",
                **config,
            }
            problem = generate_problem(topic, state)
            chosen_view = state.get("active_question_view", active_view)
            unavailable_expected = expected_unavailable(topic, config, selected_views)

            if problem is None:
                if unavailable_expected:
                    summary["expected_unavailable"] += 1
                else:
                    summary["unexpected_unavailable"] += 1
                    failures.append(
                        {
                            "topic": topic,
                            "config": config,
                            "selected_views": selected_views,
                            "active_view": active_view,
                            "message": UNAVAILABLE_PROBLEM_MESSAGE,
                        }
                    )
                continue

            options = {
                "topic_config": config,
                "questionViews": (chosen_view,),
            }
            contract = validate_problem_contract(problem, topic, options, chosen_view)
            if contract.valid:
                summary["valid"] += 1
            else:
                summary["invalid"] += 1
                failures.append(
                    {
                        "topic": topic,
                        "config": config,
                        "selected_views": selected_views,
                        "requested_active_view": active_view,
                        "chosen_view": chosen_view,
                        "contract": contract,
                        "problem": problem_summary(problem),
                    }
                )

    return summary, failures


def run_targeted_checks():
    checks = []
    raw_options = {
        "topic_config": {
            "functionFamilies": ("linear",),
            "functionStyles": ("simple",),
            "domainRestrictions": ("restricted_interval",),
        },
        "questionViews": ("equation",),
    }
    raw_problem = GENERATORS["domain_and_range"]("easy", raw_options)
    raw_contract = validate_problem_contract(raw_problem, "domain_and_range", raw_options, "equation")
    checks.append(("raw restricted interval equation fails contract", not raw_contract.valid))

    state = {
        "topic": "domain_and_range",
        "functionFamilies": ("linear",),
        "functionStyles": ("simple",),
        "domainRestrictions": ("restricted_interval",),
        "question_view_equation": "true",
        "active_question_view": "equation",
    }
    checks.append(("restricted interval equation unavailable", generate_problem("domain_and_range", state) is None))

    state = {
        "topic": "domain_and_range",
        "functionFamilies": ("square_root",),
        "functionStyles": ("simple",),
        "domainRestrictions": ("restricted_interval",),
        "question_view_equation": "true",
        "active_question_view": "equation",
    }
    square_root_problem = generate_problem("domain_and_range", state)
    checks.append(
        (
            "square root restricted interval equation passes as natural restriction",
            square_root_problem is not None
            and square_root_problem.metadata.get("domain_restriction") == "none"
            and square_root_problem.metadata.get("domain") != "(-∞, ∞)",
        )
    )

    state = {
        "topic": "domain_and_range",
        "functionFamilies": ("linear",),
        "functionStyles": ("simple",),
        "domainRestrictions": ("restricted_interval",),
        "question_view_graph": "true",
        "active_question_view": "graph",
    }
    graph_problem = generate_problem("domain_and_range", state)
    graph_features = graph_problem.graph_config.get("features", {}) if graph_problem else {}
    checks.append(
        (
            "restricted interval graph passes with domain segments",
            graph_problem is not None and bool(graph_features.get("domain_segments")),
        )
    )

    state = {
        "topic": "domain_and_range",
        "functionFamilies": ("linear",),
        "functionStyles": ("simple",),
        "domainRestrictions": ("union_of_intervals",),
        "question_view_equation": "true",
        "active_question_view": "equation",
    }
    checks.append(("union interval equation unavailable", generate_problem("domain_and_range", state) is None))

    state = {
        "topic": "domain_and_range",
        "functionFamilies": ("linear",),
        "functionStyles": ("simple",),
        "domainRestrictions": ("none",),
        "question_view_equation": "true",
        "active_question_view": "equation",
    }
    plain_problem = generate_problem("domain_and_range", state)
    plain_metadata = plain_problem.metadata if plain_problem else {}
    checks.append(
        (
            "plain equation does not force restricted answer",
            plain_problem is not None
            and plain_metadata.get("domain_restriction") == "none"
            and not plain_metadata.get("domain_segments"),
        )
    )

    return checks


def main():
    summary, failures = run_matrix()
    checks = run_targeted_checks()

    print("Problem contract smoke test")
    print(f"Summary: {summary}")
    print("Targeted checks:")
    for label, passed in checks:
        print(f"- {label}: {'PASS' if passed else 'FAIL'}")

    if failures:
        print(f"Failures: {len(failures)}")
        for failure in failures[:20]:
            print(failure)
        raise SystemExit(1)

    if not all(passed for _label, passed in checks):
        raise SystemExit(1)

    print("All problem contract checks passed.")


if __name__ == "__main__":
    main()
