import re

from services.milo.models import AITutorResponse


DEFAULT_HELP_STATUS = "hint"


def build_tutor_response(session, runtime_state, model_response, assembled_prompt):
    reply = format_tutor_reply(model_response.text, session)
    reply = apply_action_response_limits(reply, session)
    reply_messages = split_tutor_reply_messages(reply)
    return AITutorResponse(
        reply=reply,
        reply_messages=reply_messages,
        help_status=response_help_status(session, runtime_state),
        diagnosis=None,
        suggested_actions=[],
        raw_model_response=model_response,
        assembled_prompt=assembled_prompt,
    )


def response_help_status(session, runtime_state):
    if session.action_mode == "solution":
        return "solution"
    if session.action_mode == "hint":
        return "hint"
    if session.help_status == "solution":
        return "solution"
    if runtime_state.value == "solution_explanation":
        return "solution"
    return DEFAULT_HELP_STATUS


def format_tutor_reply(text, session=None):
    text = str(text or "").strip()
    if not text:
        return ""

    text = strip_markdown(text, keep_numbered_steps=asks_for_step_by_step(session))
    text = strip_latex(text)
    text = normalize_math_spacing(text)
    text = normalize_whitespace(text)
    return split_into_readable_paragraphs(text)


def asks_for_step_by_step(session):
    message = str(getattr(session, "student_message", "") or "").lower()
    return any(
        phrase in message
        for phrase in (
            "step by step",
            "step-by-step",
            "walk me through",
            "walk through",
        )
    )


def strip_markdown(text, keep_numbered_steps=False):
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if re.fullmatch(r"[-*_]{3,}", line):
            continue
        if re.match(r"^#{1,6}\s+", line):
            continue
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        if keep_numbered_steps:
            line = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", line)
        else:
            line = re.sub(r"^\s*\d+\.\s+", "", line)
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", text)
    if not keep_numbered_steps:
        text = remove_step_headings(text)
    return text


def remove_step_headings(text):
    heading_phrases = (
        "Determine the Domain",
        "Determine the Range",
        "Find the Domain",
        "Find the Range",
        "Identify Restrictions",
        "Look at the Equation",
        "Analyze the Equation",
        "Check the Graph",
    )
    for phrase in heading_phrases:
        text = re.sub(rf"\bStep\s+\d+\s*:\s*{phrase}\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bStep\s+\d+\s*:\s*", "", text, flags=re.IGNORECASE)
    return re.sub(r"\bstep by step\b", "", text, flags=re.IGNORECASE)


def strip_latex(text):
    text = re.sub(r"\$\$([\s\S]*?)\$\$", r"\1", text)
    text = re.sub(r"\$([^$\n]+)\$", r"\1", text)
    text = re.sub(r"\\\(([\s\S]*?)\\\)", r"\1", text)
    text = re.sub(r"\\\[([\s\S]*?)\\\]", r"\1", text)

    replacements = {
        r"\left": "",
        r"\right": "",
        r"\cdot": "·",
        r"\times": "×",
        r"\div": "÷",
        r"\infty": "∞",
        r"\leq": "≤",
        r"\le": "≤",
        r"\geq": "≥",
        r"\ge": "≥",
        r"\neq": "≠",
        r"\ne": "≠",
        r"\lt": "<",
        r"\gt": ">",
    }
    for latex, plain in replacements.items():
        text = text.replace(latex, plain)

    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"\1/\2", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", text)
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace("$", "")
    text = convert_common_exponents(text)
    return text


def convert_common_exponents(text):
    superscripts = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }

    def replace_braced(match):
        exponent = match.group(1)
        if all(char in superscripts for char in exponent):
            return "".join(superscripts[char] for char in exponent)
        return f"^{exponent}"

    def replace_single(match):
        return superscripts.get(match.group(1), f"^{match.group(1)}")

    text = re.sub(r"\^\{([^{}]+)\}", replace_braced, text)
    return re.sub(r"\^([0-9])", replace_single, text)


def normalize_math_spacing(text):
    text = re.sub(r"[ \t]*=[ \t]*", " = ", text)
    text = re.sub(r"[ \t]*([<>≤≥≠])[ \t]*", r" \1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]+([.,!?;:])", r"\1", text)
    text = re.sub(r"\(\s*-\s*∞\s*,\s*∞\s*\)", "(-∞, ∞)", text)
    text = re.sub(r"\(\s*-\s*infty\s*,\s*infty\s*\)", "(-∞, ∞)", text, flags=re.IGNORECASE)
    return text.strip()


def normalize_whitespace(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_readable_paragraphs(text):
    existing = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    paragraphs = []
    for part in existing or [text]:
        paragraphs.extend(paragraphs_from_block(part))
    return "\n\n".join(paragraphs).strip()


def split_tutor_reply_messages(reply):
    parts = [part.strip() for part in re.split(r"\n{2,}", str(reply or "")) if part.strip()]
    messages = []
    for part in parts:
        messages.extend(chat_messages_from_paragraph(part))
    return messages or ([str(reply).strip()] if str(reply or "").strip() else [])


def chat_messages_from_paragraph(paragraph):
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    if not paragraph:
        return []
    if len(paragraph) <= 170:
        return [paragraph]

    sentences = sentence_split(paragraph)
    if len(sentences) <= 1:
        return [paragraph]

    messages = []
    current = []
    current_length = 0
    for sentence in sentences:
        length = len(sentence)
        should_flush = current and (
            current_length + length > 170
            or starts_new_chat_bubble(sentence)
        )
        if should_flush:
            messages.append(" ".join(current).strip())
            current = []
            current_length = 0
        current.append(sentence)
        current_length += length
    if current:
        messages.append(" ".join(current).strip())
    return messages


def paragraphs_from_block(block):
    block = re.sub(r"\s+", " ", block).strip()
    if not block:
        return []

    sentences = sentence_split(block)
    paragraphs = []
    current = []
    current_length = 0

    for sentence in sentences:
        length = len(sentence)
        should_flush = current and (
            current_length + length > 180
            or starts_new_tutor_thought(sentence)
        )
        if should_flush:
            paragraphs.append(" ".join(current).strip())
            current = []
            current_length = 0
        current.append(sentence)
        current_length += length

    if current:
        paragraphs.append(" ".join(current).strip())
    return paragraphs


def sentence_split(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text)
    return [part.strip() for part in parts if part.strip()]


def starts_new_tutor_thought(sentence):
    return bool(
        re.match(
            r"^(Now|Next|Then|Start|Check|Use|For all|The first|The domain|The range|Can you|Ask yourself|Think about|Look at|For example|Based on|What does|Division by|That is why|That means)\b",
            sentence,
        )
    )


def starts_new_chat_bubble(sentence):
    return starts_new_tutor_thought(sentence) or bool(
        re.match(
            r"^(So|That means|In this example|For this problem|Looking back|When x|When the graph|A similar example|Here is a similar example)\b",
            sentence,
        )
    )


def apply_action_response_limits(reply, session):
    action_mode = str(getattr(session, "action_mode", "chat") or "chat")
    if action_mode == "hint":
        return limited_sentences(reply, 2)
    if action_mode == "solution":
        return limited_sentences(reply, 3)
    return reply


def limited_sentences(text, limit):
    sentences = sentence_split(str(text or "").strip())
    if not sentences:
        return str(text or "").strip()
    return " ".join(sentences[:limit]).strip()
