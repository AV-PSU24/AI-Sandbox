from dataclasses import dataclass, field
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from random import randint
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).parent
PORT = int(os.environ.get("PORT", "8010"))

UNITS = {
    "unit1": {
        "label": "Unit 1: Functions and Graphs",
        "topics": [
            ("evaluating_functions", "Evaluating functions"),
            ("domain_and_range", "Domain and range"),
            ("parent_functions", "Parent functions"),
        ],
    }
}

DIFFICULTIES = ("easy", "medium", "hard")


@dataclass
class Problem:
    topic: str
    problem_type: str
    difficulty: str
    display_equation: str
    prompt: str
    answer_fields: list[dict] = field(default_factory=list)
    correct_answer: str = ""
    acceptable_answers: list[str] = field(default_factory=list)
    hint: str = ""
    solution: str = ""
    metadata: dict = field(default_factory=dict)
    assets: list[dict] = field(default_factory=list)

    @property
    def question(self):
        return "\n\n".join(part for part in (self.display_equation, self.prompt) if part)

    @property
    def answer(self):
        return self.correct_answer

    def to_dict(self):
        return {
            "topic": self.topic,
            "problem_type": self.problem_type,
            "difficulty": self.difficulty,
            "display_equation": self.display_equation,
            "prompt": self.prompt,
            "answer_fields": self.answer_fields,
            "correct_answer": self.correct_answer,
            "acceptable_answers": self.acceptable_answers,
            "hint": self.hint,
            "solution": self.solution,
            "metadata": self.metadata,
            "assets": self.assets,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            data = {}

        def text_field(name):
            value = data.get(name, "")
            return "" if value is None else str(value)

        correct_answer = text_field("correct_answer")
        acceptable_answers = data.get("acceptable_answers") or [correct_answer]
        if not isinstance(acceptable_answers, list):
            acceptable_answers = [acceptable_answers]
        answer_fields = data.get("answer_fields")
        if not isinstance(answer_fields, list):
            answer_fields = [{"name": "answer", "label": "Answer", "type": "text"}]

        return cls(
            topic=text_field("topic"),
            problem_type=text_field("problem_type"),
            difficulty=text_field("difficulty"),
            display_equation=text_field("display_equation"),
            prompt=text_field("prompt"),
            answer_fields=answer_fields,
            correct_answer=correct_answer,
            acceptable_answers=[str(answer) for answer in acceptable_answers],
            hint=text_field("hint"),
            solution=text_field("solution"),
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else {},
            assets=data.get("assets") if isinstance(data.get("assets"), list) else [],
        )


def signed(value):
    return f"- {abs(value)}" if value < 0 else f"+ {value}"


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


def superscript_number(value):
    digits = str(value)
    superscripts = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    return digits.translate(superscripts)


def polynomial_term(coefficient, exponent, is_first):
    sign = "-" if coefficient < 0 else "+"
    absolute = abs(coefficient)

    if exponent == 0:
        body = str(absolute)
    elif exponent == 1:
        body = "x" if absolute == 1 else f"{absolute}x"
    else:
        body = f"x{superscript_number(exponent)}" if absolute == 1 else f"{absolute}x{superscript_number(exponent)}"

    if is_first:
        return f"-{body}" if sign == "-" else body
    return f" {sign} {body}"


def format_function_equation(coefficients):
    degree = len(coefficients) - 1
    terms = []
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        terms.append(polynomial_term(coefficient, degree - index, not terms))
    return f"f(x) = {''.join(terms) if terms else '0'}"


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


def format_function_substitution(coefficients, x):
    degree = len(coefficients) - 1
    pieces = []
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        if coefficient == 0:
            continue

        absolute = abs(coefficient)
        if exponent == 0:
            body = str(absolute)
        elif exponent == 1:
            body = f"{absolute}({x})"
        else:
            body = f"{absolute}({x}){superscript_number(exponent)}"

        if not pieces:
            pieces.append(f"-{body}" if coefficient < 0 else body)
        else:
            pieces.append(f" {'-' if coefficient < 0 else '+'} {body}")
    return "".join(pieces) if pieces else "0"


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


def topic_label(topic):
    for unit in UNITS.values():
        for value, label in unit["topics"]:
            if value == topic:
                return label
    return "Evaluating functions"


def unit_label(unit):
    return UNITS.get(unit, UNITS["unit1"])["label"]


def valid_topic_for_unit(unit, topic):
    return topic in {value for value, _label in UNITS[unit]["topics"]}


def normalize(value):
    return "".join(str(value).lower().split())


def count_value(state, key):
    try:
        return max(0, int(state.get(key, "0")))
    except ValueError:
        return 0


def answers_match(user_answer, correct_answer):
    user = normalize(user_answer)
    correct = normalize(correct_answer)

    if user == correct:
        return True

    try:
        return abs(float(user) - float(correct)) < 0.001
    except ValueError:
        pass

    if "," in correct:
        return sorted(user.split(",")) == sorted(correct.split(","))

    return False


def answers_match_problem(user_answer, problem):
    return any(answers_match(user_answer, answer) for answer in problem.acceptable_answers)


def encoded_json(value):
    return escape(json.dumps(value))


def encoded_problem(problem):
    return encoded_json(problem.to_dict())


def decoded_json(value, fallback):
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def problem_from_form(data):
    return Problem.from_dict(decoded_json(data.get("problem_json"), {}))


def render_asset(asset):
    if not isinstance(asset, dict):
        return ""
    asset_type = asset.get("type", "")
    if asset_type == "image" and asset.get("src"):
        alt = asset.get("alt", "")
        return f'<img src="{escape(asset["src"])}" alt="{escape(alt)}">'
    if asset_type == "text" and asset.get("content"):
        return escape(asset["content"])
    return ""


def render_problem_display(problem):
    parts = []
    if problem.display_equation:
        parts.append(escape(problem.display_equation))
    if problem.prompt:
        parts.append(escape(problem.prompt))
    for asset in problem.assets:
        rendered_asset = render_asset(asset)
        if rendered_asset:
            parts.append(rendered_asset)
    return "<br><br>".join(parts)


def select_options(options, selected):
    html = []
    for value, label in options:
        selected_attr = " selected" if value == selected else ""
        html.append(f'<option value="{escape(value)}"{selected_attr}>{escape(label)}</option>')
    return "\n".join(html)


def custom_dropdown(name, label, options, selected):
    selected_label = next((option_label for value, option_label in options if value == selected), options[0][1])
    option_markup = []
    for index, (value, option_label) in enumerate(options):
        is_selected = value == selected
        option_markup.append(
            f"""
            <button
              class="custom-option"
              id="{escape(name)}-option-{index}"
              role="option"
              type="button"
              data-value="{escape(value)}"
              aria-selected="{str(is_selected).lower()}"
              tabindex="-1"
            >{escape(option_label)}</button>"""
        )

    return f"""
        <div class="field custom-select" data-dropdown>
          <span class="field-label" id="{escape(name)}-label">{escape(label)}</span>
          <input type="hidden" name="{escape(name)}" value="{escape(selected)}">
          <button
            class="custom-select-trigger"
            type="button"
            aria-haspopup="listbox"
            aria-expanded="false"
            aria-labelledby="{escape(name)}-label {escape(name)}-value"
          >
            <span id="{escape(name)}-value" data-selected-label>{escape(selected_label)}</span>
            <span class="select-chevron" aria-hidden="true"></span>
          </button>
          <div class="custom-options" role="listbox" aria-labelledby="{escape(name)}-label">
            {''.join(option_markup)}
          </div>
        </div>"""


def reset_for_new_problem(state):
    unit = state["unit"] if state["unit"] in UNITS else "unit1"
    topic = state["topic"] if valid_topic_for_unit(unit, state["topic"]) else UNITS[unit]["topics"][0][0]
    difficulty = state["difficulty"] if state["difficulty"] in DIFFICULTIES else "easy"
    next_problem = GENERATORS[topic](difficulty)

    state["unit"] = unit
    state["topic"] = topic
    state["difficulty"] = difficulty
    state["problem"] = next_problem
    state["answer"] = next_problem.answer
    state["hint_visible"] = ""
    state["solution_visible"] = ""
    state["answered"] = ""
    state["feedback"] = ""
    state["feedback_type"] = "empty"


def page_context(state):
    unit = state.get("unit", "unit1")
    if unit not in UNITS:
        unit = "unit1"

    difficulty = state.get("difficulty", "easy")
    if difficulty not in DIFFICULTIES:
        difficulty = "easy"

    topic = state.get("topic") or UNITS[unit]["topics"][0][0]
    if not valid_topic_for_unit(unit, topic):
        topic = UNITS[unit]["topics"][0][0]

    problem = state.get("problem")
    feedback = state.get("feedback", "")
    feedback_type = state.get("feedback_type", "empty")
    hint_visible = state.get("hint_visible", "") == "true"
    solution_visible = state.get("solution_visible", "") == "true"
    answered = state.get("answered", "") == "true"
    correct_count = count_value(state, "correct_count")
    hint_count = count_value(state, "hint_count")
    incorrect_count = count_value(state, "incorrect_count")
    skip_count = count_value(state, "skip_count")
    generated = state.get("generated", "") == "true"

    if problem is None:
        problem = GENERATORS[topic](difficulty)

    return {
        "unit": unit,
        "topic": topic,
        "difficulty": difficulty,
        "problem": problem,
        "feedback": feedback,
        "feedback_type": feedback_type,
        "hint_visible": hint_visible,
        "solution_visible": solution_visible,
        "answered": answered,
        "correct_count": correct_count,
        "hint_count": hint_count,
        "incorrect_count": incorrect_count,
        "skip_count": skip_count,
        "generated": generated,
    }


def render_control_panel(context):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    unit_options = tuple((value, data["label"]) for value, data in UNITS.items())
    topic_options = tuple(UNITS[unit]["topics"])
    difficulty_options = tuple((item, item.title()) for item in DIFFICULTIES)
    unit_dropdown = custom_dropdown("unit", "Unit", unit_options, unit)
    topic_dropdown = custom_dropdown("topic", "Topic", topic_options, topic)
    difficulty_dropdown = custom_dropdown("difficulty", "Difficulty", difficulty_options, difficulty)
    generate_disabled = " disabled" if context["generated"] else ""

    return f"""      <form class="control-panel" action="/generate" method="get">
        <div class="panel-title">
          <span>MathPrac AI</span>
        </div>
        <input type="hidden" name="correct_count" value="{context["correct_count"]}">
        <input type="hidden" name="hint_count" value="{context["hint_count"]}">
        <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
        <input type="hidden" name="skip_count" value="{context["skip_count"]}">
        {unit_dropdown}
        {topic_dropdown}
        {difficulty_dropdown}
        <button type="submit" data-generate-button{generate_disabled}>Generate Practice Problems</button>
      </form>"""


def render_answer_form(context):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]
    answered = context["answered"]
    generated = context["generated"]
    correct_checked = context["feedback_type"] == "correct"
    hint_disabled = " disabled" if hint_visible or solution_visible or correct_checked else ""
    solution_disabled = " disabled" if solution_visible or correct_checked else ""
    skip_disabled = " disabled" if solution_visible or correct_checked else ""
    check_disabled = " disabled" if solution_visible or correct_checked else ""
    next_disabled = "" if correct_checked or solution_visible else " disabled"

    return f"""        <form class="answer-panel" action="/check" method="post">
          <input type="hidden" name="unit" value="{escape(unit)}">
          <input type="hidden" name="topic" value="{escape(topic)}">
          <input type="hidden" name="difficulty" value="{escape(difficulty)}">
          <input type="hidden" name="problem_json" value="{encoded_problem(problem)}">
          <input type="hidden" name="hint_visible" value="{str(hint_visible).lower()}">
          <input type="hidden" name="solution_visible" value="{str(solution_visible).lower()}">
          <input type="hidden" name="answered" value="{str(answered).lower()}">
          <input type="hidden" name="correct_count" value="{context["correct_count"]}">
          <input type="hidden" name="hint_count" value="{context["hint_count"]}">
          <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
          <input type="hidden" name="skip_count" value="{context["skip_count"]}">
          <input type="hidden" name="generated" value="{str(generated).lower()}">
          <label for="user_answer">answer_input</label>
          <div class="answer-row">
            <input id="user_answer" name="user_answer" type="text" autocomplete="off" placeholder="type answer">
            <button name="action" value="check" type="submit"{check_disabled}>Check</button>
          </div>
          <div class="utility-row">
            <button name="action" value="hint" type="submit"{hint_disabled}>Hint</button>
            <button name="action" value="skip" type="submit"{skip_disabled}>Skip</button>
            <button name="action" value="solution" type="submit"{solution_disabled}>Solution</button>
            <button name="action" value="next" type="submit"{next_disabled}>Next Problem</button>
          </div>
        </form>"""


def render_feedback(context):
    return f"""        <div class="feedback {escape(context["feedback_type"])}">{escape(context["feedback"])}</div>"""


def render_help_stack(context):
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]

    return f"""        <div class="help-stack">
          {f'<div class="help-box hint-box">{escape(problem.hint)}</div>' if hint_visible else ''}
          {f'<div class="help-box solution-box">{escape(problem.solution)} Answer: {escape(problem.answer)}</div>' if solution_visible else ''}
        </div>"""


def render_stats(context):
    return f"""        <div class="stats-panel" aria-label="Practice stats">
          <span class="stat-correct">Correct: {context["correct_count"]}</span>
          <span class="stat-hints">Hints: {context["hint_count"]}</span>
          <span class="stat-incorrect">Incorrect: {context["incorrect_count"]}</span>
          <span class="stat-skips">Skips: {context["skip_count"]}</span>
        </div>"""


def render_problem_panel(context):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    problem = context["problem"]
    answer_form = render_answer_form(context)
    feedback = render_feedback(context)
    help_stack = render_help_stack(context)
    stats = render_stats(context)

    return f"""      <section class="problem-panel" aria-live="polite">
        <div class="badges">
          <span>Algebra 2</span>
          <span data-badge="unit">{escape(unit_label(unit))}</span>
          <span data-badge="topic">{escape(topic_label(topic))}</span>
          <span data-badge="difficulty">{escape(difficulty.title())}</span>
        </div>

        <h1>{render_problem_display(problem)}</h1>

{answer_form}

{feedback}
{help_stack}
{stats}
      </section>"""


def render_page(state):
    context = page_context(state)
    control_panel = render_control_panel(context)
    problem_panel = render_problem_panel(context)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MathPracAI</title>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js" defer></script>
</head>
<body>
  <main class="app-frame">
    <section class="generator">
{control_panel}

{problem_panel}
    </section>
  </main>
</body>
</html>"""


def parse_post(handler):
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length).decode("utf-8")
    return {key: values[0] for key, values in parse_qs(body).items()}


class MathPracHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/styles.css":
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.end_headers()
            self.wfile.write((ROOT / "styles.css").read_bytes())
            return

        if parsed.path == "/script.js":
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.end_headers()
            self.wfile.write((ROOT / "script.js").read_bytes())
            return

        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        if parsed.path in ("/", "/generate"):
            if parsed.path == "/generate":
                unit = query.get("unit", "unit1")
                difficulty = query.get("difficulty", "easy")
                topic = query.get("topic", "")
                if unit not in UNITS:
                    unit = "unit1"
                if difficulty not in DIFFICULTIES:
                    difficulty = "easy"
                if not valid_topic_for_unit(unit, topic):
                    topic = UNITS[unit]["topics"][0][0]
                query["unit"] = unit
                query["topic"] = topic
                query["difficulty"] = difficulty
                query["problem"] = GENERATORS[topic](difficulty)
                query["feedback"] = ""
                query["feedback_type"] = "empty"
                query["hint_visible"] = ""
                query["solution_visible"] = ""
                query["answered"] = ""
                query["generated"] = "true"
            self.respond(render_page(query))
            return

        self.send_error(404)

    def do_POST(self):
        if self.path != "/check":
            self.send_error(404)
            return

        data = parse_post(self)
        problem = problem_from_form(data)
        action = data.get("action", "check")
        user_answer = data.get("user_answer", "")
        state = {
            "unit": data.get("unit", "unit1"),
            "topic": data.get("topic", "evaluating_functions"),
            "difficulty": data.get("difficulty", "easy"),
            "problem": problem,
            "answer": problem.answer,
            "hint_visible": data.get("hint_visible", ""),
            "solution_visible": data.get("solution_visible", ""),
            "answered": data.get("answered", ""),
            "correct_count": data.get("correct_count", "0"),
            "hint_count": data.get("hint_count", "0"),
            "incorrect_count": data.get("incorrect_count", "0"),
            "skip_count": data.get("skip_count", "0"),
            "generated": data.get("generated", "true"),
        }

        if action == "hint":
            state["feedback"] = ""
            state["feedback_type"] = "empty"
            state["hint_visible"] = "true"
            state["hint_count"] = str(count_value(state, "hint_count") + 1)
        elif action == "solution":
            state["feedback"] = ""
            state["feedback_type"] = "empty"
            state["solution_visible"] = "true"
            state["answered"] = "true"
        elif action == "next":
            reset_for_new_problem(state)
            state["generated"] = "true"
        elif action == "skip":
            state["skip_count"] = str(count_value(state, "skip_count") + 1)
            reset_for_new_problem(state)
            state["generated"] = "true"
        elif answers_match_problem(user_answer, problem):
            state["feedback"] = "Correct."
            state["feedback_type"] = "correct"
            state["correct_count"] = str(count_value(state, "correct_count") + 1)
            state["answered"] = "true"
        else:
            state["feedback"] = "Not quite. Try again or open the hint."
            state["feedback_type"] = "incorrect"
            state["incorrect_count"] = str(count_value(state, "incorrect_count") + 1)
            state["answered"] = "true"

        self.respond(render_page(state))

    def respond(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", PORT), MathPracHandler)
    print(f"MathPracAI running at http://localhost:{PORT}")
    server.serve_forever()
