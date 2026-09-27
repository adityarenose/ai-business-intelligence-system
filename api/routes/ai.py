"""Natural-language business assistant endpoint."""

from flask import Blueprint, jsonify, request

from src.ai_assistant import AssistantError, ask_business_question

ai_bp = Blueprint("ai", __name__, url_prefix="/api")


@ai_bp.post("/ask")
def ask():
    if not request.is_json:
        return jsonify({"error": {"code": "invalid_content_type", "message": "Content-Type must be application/json."}}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise AssistantError("Request body must be a JSON object.")
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise AssistantError("'question' must be a non-empty string.")

    return jsonify(ask_business_question(question))
