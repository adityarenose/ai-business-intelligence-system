from api.app import create_app


SAMPLE_CUSTOMER = {
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
    "segment": "At Risk",
    "payment_method": "UPI",
}


def test_api_endpoints_return_json_and_successful_data():
    client = create_app({"TESTING": True}).test_client()
    endpoints = [
        "/api/health",
        "/api/summary",
        "/api/sales/trend",
        "/api/sales/categories",
        "/api/sales/products",
        "/api/sales/cities",
        "/api/customers/segments",
        "/api/customers/churn",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, endpoint
        assert response.is_json, endpoint
        assert "data" in response.get_json() or endpoint == "/api/health"


def test_predict_churn_returns_prediction():
    client = create_app({"TESTING": True}).test_client()
    response = client.post("/api/predict-churn", json=SAMPLE_CUSTOMER)

    assert response.status_code == 200
    assert response.is_json
    assert set(response.get_json()["data"]) == {
        "churn_probability",
        "predicted_class",
        "risk_level",
    }


def test_predict_churn_validates_missing_fields_and_content_type():
    client = create_app({"TESTING": True}).test_client()

    missing_field = client.post("/api/predict-churn", json={"age": 31})
    assert missing_field.status_code == 400
    assert missing_field.get_json()["error"]["code"] == "validation_error"

    wrong_content_type = client.post(
        "/api/predict-churn", data='{"age": 31}', content_type="text/plain"
    )
    assert wrong_content_type.status_code == 415
    assert wrong_content_type.get_json()["error"]["code"] == "invalid_content_type"

    invalid_age = dict(SAMPLE_CUSTOMER, age=150)
    response = client.post("/api/predict-churn", json=invalid_age)
    assert response.status_code == 400
    assert "between 18 and 100" in response.get_json()["error"]["message"]

    invalid_number = dict(SAMPLE_CUSTOMER, monthly_spend=float("nan"))
    response = client.post("/api/predict-churn", json=invalid_number)
    assert response.status_code == 400


def test_unknown_endpoint_returns_json_error():
    client = create_app({"TESTING": True}).test_client()
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
