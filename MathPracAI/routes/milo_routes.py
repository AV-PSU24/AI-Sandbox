from flask import Blueprint, jsonify, request

from services.milo.service import AITutorError, create_tutor_reply


milo_bp = Blueprint("milo", __name__, url_prefix="/ai-tutor")


@milo_bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    student_message = str(data.get("studentMessage") or "").strip()
    if not student_message:
        return jsonify({"ok": False, "error": "studentMessage is required."}), 400

    try:
        return jsonify(create_tutor_reply(student_message, data))
    except AITutorError as error:
        return jsonify({"ok": False, "error": str(error)}), 502
