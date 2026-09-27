"""Churn prediction endpoint."""

from flask import Blueprint, jsonify, request

from api.services.prediction_service import predict_customer_churn

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api")


@prediction_bp.post("/predict-churn")
def predict_churn():
    if not request.is_json:
        return jsonify({"error": {"code": "invalid_content_type", "message": "Content-Type must be application/json."}}), 415

    result = predict_customer_churn(request.get_json(silent=True))
    return jsonify({"data": result})
