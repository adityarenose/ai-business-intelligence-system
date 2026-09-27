from src.analytics import load_business_data
from src.feature_engineering import build_customer_features
from src.ml_model import predict_churn
from src.feature_engineering import prepare_customer_dataset


def test_customer_features_include_target_and_expected_columns():
    data = load_business_data()
    features = build_customer_features(
        customers_df=data["customers"],
        orders_df=data["orders"],
        order_items_df=data["order_items"],
        products_df=data["products"],
    )

    assert "churn" in features.columns
    assert {"age", "tenure_months", "monthly_spend", "purchase_frequency", "support_calls"}.issubset(set(features.columns))
    assert features.shape[0] > 0


def test_predict_churn_returns_probability_class_and_risk():
    sample_customer = {
        "customer_id": 999999,
        "age": 31,
        "gender": "Female",
        "city": "Bengaluru",
        "tenure_months": 7,
        "monthly_spend": 3500,
        "support_calls": 6,
        "purchase_frequency": 1.2,
        "total_orders": 2,
        "total_spent": 4200,
        "avg_order_value": 2100,
        "payment_method": "UPI",
        "customer_segment": "At Risk",
    }

    prediction = predict_churn(sample_customer)

    assert set(prediction.keys()) == {"churn_probability", "predicted_class", "risk_level"}
    assert 0.0 <= prediction["churn_probability"] <= 1.0
    assert prediction["predicted_class"] in {0, 1}
    assert prediction["risk_level"] in {"Low", "Medium", "High"}


def test_model_segment_does_not_use_churn_target():
    data = load_business_data()
    original = data["customers"].copy()
    changed = original.copy()
    changed["churn"] = 1 - changed["churn"]

    original_features = prepare_customer_dataset(original, data["orders"])
    changed_features = prepare_customer_dataset(changed, data["orders"])

    assert original_features["segment"].equals(changed_features["segment"])
