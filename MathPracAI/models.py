from dataclasses import dataclass, field
from html import escape
import json


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
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        assets = data.get("assets")
        if not isinstance(assets, list):
            assets = []

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
            metadata=metadata,
            assets=assets,
        )


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
