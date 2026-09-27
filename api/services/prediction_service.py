"""Validation and orchestration for churn predictions."""

from __future__ import annotations

import math
from numbers import Real
from typing import Any

from src.ml_model import load_model


NUMERIC_FIELDS = {
    "age",
    "tenure_months",
    "monthly_spend",
    "support_calls",
    "purchase_frequency",
    "total_orders",
    "total_spent",
    "avg_order_value",
}
ALLOWED_GENDERS = {"Male", "Female", "Other"}
ALLOWED_SEGMENTS = {"High Value", "Medium Value", "Low Value", "At Risk"}
ALLOWED_PAYMENT_METHODS = {"UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Net Banking"}


def validate_prediction_payload(payload: Any) -> dict[str, Any]:
    """Validate a prediction body and return a normalized dictionary."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    if not payload:
        raise ValueError("Request body cannot be empty.")

    model = load_model()
    missing = [field for field in model.feature_names if field not in payload]
    if missing:
        raise ValueError(f"Missing required input features: {missing}")

    for field in NUMERIC_FIELDS.intersection(model.feature_names):
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"'{field}' must be numeric.")
        if not math.isfinite(float(value)):
            raise ValueError(f"'{field}' must be finite.")
        if field == "age" and not 18 <= value <= 100:
            raise ValueError("'age' must be between 18 and 100.")
        if field != "age" and value < 0:
            raise ValueError(f"'{field}' cannot be negative.")

    if "gender" in model.feature_names and payload["gender"] not in ALLOWED_GENDERS:
        raise ValueError("'gender' is not a supported value.")
    if "segment" in model.feature_names and payload["segment"] not in ALLOWED_SEGMENTS:
        raise ValueError("'segment' is not a supported value.")
    if "payment_method" in model.feature_names and payload["payment_method"] not in ALLOWED_PAYMENT_METHODS:
        raise ValueError("'payment_method' is not a supported value.")
    for field in {"city", "gender", "segment", "payment_method"}.intersection(model.feature_names):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValueError(f"'{field}' must be a non-empty string.")

    return {field: payload[field] for field in model.feature_names}


def predict_customer_churn(payload: Any) -> dict[str, Any]:
    customer_data = validate_prediction_payload(payload)
    return load_model().predict_risk(customer_data)
