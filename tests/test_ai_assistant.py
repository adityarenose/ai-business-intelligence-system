import pytest

from api.app import create_app
from src.ai_assistant import (
    BusinessAssistant,
    LLMResponseError,
    validate_read_only_sql,
)


class MalformedProvider:
    def generate(self, question, data, insights):
        return {"answer": 123, "insights": "not a list"}


class GroundedProvider:
    def generate(self, question, data, insights):
        return {
            "answer": "Grounded provider answer.",
            "insights": ["Provider used verified records."],
            "recommendations": ["Review the returned records."],
        }


def test_valid_business_question_returns_grounded_response():
    response = BusinessAssistant().ask("Which category generated the most revenue?")

    assert set(response) == {"question", "answer", "data", "insights", "recommendations"}
    assert response["data"]
    assert "revenue" in response["answer"].lower()


def test_provider_can_only_rephrase_verified_tool_results():
    response = BusinessAssistant(provider=GroundedProvider()).ask(
        "Which city has the highest sales?"
    )

    assert response["answer"] != "Grounded provider answer."
    assert "sales" in response["answer"].lower()
    assert response["data"]
    assert response["insights"] == ["Cities are ranked by order revenue."]


def test_unavailable_information_is_explicit():
    response = BusinessAssistant().ask("What is the weather in Bengaluru today?")

    assert response["data"] == []
    assert "unavailable" in response["answer"].lower()
    assert response["recommendations"] == []


def test_malformed_llm_response_falls_back_to_grounded_result():
    response = BusinessAssistant(provider=MalformedProvider()).ask(
        "How many customers have churned?"
    )

    assert response["data"]
    assert "customers have churned" in response["answer"]


def test_dangerous_sql_is_rejected():
    dangerous_queries = [
        "INSERT INTO customers VALUES (1)",
        "SELECT * FROM customers; DROP TABLE customers",
        "UPDATE customers SET churn = 0",
        "DELETE FROM customers",
        "ALTER TABLE customers ADD COLUMN secret TEXT",
        "TRUNCATE TABLE customers",
    ]

    for query in dangerous_queries:
        with pytest.raises(ValueError):
            validate_read_only_sql(query)


def test_ai_endpoint_validates_questions_and_returns_contract():
    client = create_app({"TESTING": True}).test_client()

    valid = client.post(
        "/api/ask", json={"question": "What are our top 10 products?"}
    )
    assert valid.status_code == 200
    assert set(valid.get_json()) == {
        "question",
        "answer",
        "data",
        "insights",
        "recommendations",
    }
    assert len(valid.get_json()["data"]) == 10

    invalid = client.post("/api/ask", json={"question": ""})
    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "validation_error"

    wrong_type = client.post("/api/ask", json={"question": 42})
    assert wrong_type.status_code == 400
    assert wrong_type.get_json()["error"]["code"] == "validation_error"


def test_ai_endpoint_rejects_non_json_requests():
    client = create_app({"TESTING": True}).test_client()
    response = client.post("/api/ask", data="question=hello")

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "invalid_content_type"
