from dataclasses import dataclass
from random import randint

from formatters import format_function_equation, format_function_substitution, signed
from models import Problem


@dataclass(frozen=True)
class EvaluatingFunctionsProblemType:
    topic: str = "evaluating_functions"
    problem_type: str = "evaluate_function"
    supported_families: tuple[str, ...] = ("linear", "quadratic", "polynomial")

    def degree_for(self, difficulty):
        if difficulty == "easy":
            return randint(1, 2)
        if difficulty == "medium":
            return randint(2, 3)
        return randint(4, 5)

    def family_for_degree(self, degree):
        if degree == 1:
            return "linear"
        if degree == 2:
            return "quadratic"
        return "polynomial"

    def generate(self, difficulty):
        degree = self.degree_for(difficulty)
        family = self.family_for_degree(degree)
        coefficient_limit = 4 if difficulty == "easy" else 7
        input_value = randint(-4 if difficulty != "easy" else 1, 6 if difficulty == "easy" else 8)
        coefficients = [randint(1, coefficient_limit)]
        for _exponent in range(degree - 1, -1, -1):
            coefficients.append(randint(-10, 10))

        return {
            "family": family,
            "coefficients": coefficients,
            "input_value": input_value,
            "correct_answer": evaluate_polynomial(coefficients, input_value),
        }


EVALUATING_FUNCTIONS_PROBLEM_TYPE = EvaluatingFunctionsProblemType()


def evaluate_polynomial(coefficients, x):
    value = 0
    degree = len(coefficients) - 1
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        value += coefficient * (x**exponent)
    return value


def create_problem(
    topic,
    problem_type,
    difficulty,
    display_equation,
    prompt,
    answer_fields,
    correct_answer,
    acceptable_answers,
    hint,
    solution,
    metadata=None,
    assets=None,
):
    answers = [str(answer) for answer in acceptable_answers]
    correct = str(correct_answer)
    if correct not in answers:
        answers.insert(0, correct)

    return Problem(
        topic=topic,
        problem_type=problem_type,
        difficulty=difficulty,
        display_equation=display_equation,
        prompt=prompt,
        answer_fields=answer_fields,
        correct_answer=correct,
        acceptable_answers=answers,
        hint=hint,
        solution=solution,
        metadata=metadata or {},
        assets=assets or [],
    )


def render_evaluating_functions_problem(data, difficulty):
    coefficients = data["coefficients"]
    input_value = data["input_value"]
    correct_answer = data["correct_answer"]
    equation = format_function_equation(coefficients)
    prompt = f"Evaluate f({input_value})."
    substitution = format_function_substitution(coefficients, input_value)

    return create_problem(
        topic=EVALUATING_FUNCTIONS_PROBLEM_TYPE.topic,
        problem_type=EVALUATING_FUNCTIONS_PROBLEM_TYPE.problem_type,
        difficulty=difficulty,
        display_equation=equation,
        prompt=prompt,
        answer_fields=[{"name": "value", "label": "Answer", "type": "text"}],
        correct_answer=correct_answer,
        acceptable_answers=[correct_answer],
        hint="Substitute the input value anywhere x appears.",
        solution=f"f({input_value}) = {substitution} = {correct_answer}.",
        metadata=data,
    )


def evaluating_functions(difficulty):
    data = EVALUATING_FUNCTIONS_PROBLEM_TYPE.generate(difficulty)
    return render_evaluating_functions_problem(data, difficulty)


def domain_and_range(difficulty):
    start = randint(-8, 4)
    equation = f"f(x) = sqrt(x {signed(-start)})"
    return create_problem(
        topic="domain_and_range",
        problem_type="square_root_domain",
        difficulty=difficulty,
        display_equation=equation,
        prompt="State the domain. Use x>=a format.",
        answer_fields=[{"name": "domain", "label": "Domain", "type": "text"}],
        correct_answer=f"x>={start}",
        acceptable_answers=[f"x>={start}"],
        hint="For a square root, the expression inside the radical must be greater than or equal to 0.",
        solution=f"x {signed(-start)} >= 0, so x >= {start}.",
        metadata={
            "function_family": "square_root",
            "domain_start": start,
        },
    )


def parent_functions(difficulty):
    choices = [
        ("y = (x - 3)^2 + 4", "quadratic"),
        ("y = |x + 2| - 5", "absolute value"),
        ("y = sqrt(x - 1)", "square root"),
        ("y = 2^(x - 4)", "exponential"),
    ]
    equation, answer = choices[randint(0, len(choices) - 1)]
    return create_problem(
        topic="parent_functions",
        problem_type="identify_parent_family",
        difficulty=difficulty,
        display_equation=equation,
        prompt="Identify the parent function family.",
        answer_fields=[{"name": "family", "label": "Family", "type": "text"}],
        correct_answer=answer,
        acceptable_answers=[answer],
        hint="Ignore shifts, stretches, and reflections. Focus on the core shape.",
        solution=f"The core function family is {answer}.",
        metadata={},
    )


GENERATORS = {
    "evaluating_functions": evaluating_functions,
    "domain_and_range": domain_and_range,
    "parent_functions": parent_functions,
}
