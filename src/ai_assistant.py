"""Grounded business-question assistant with safe, approved analytics tools.

The assistant never executes model-generated code. Questions are mapped to a
small allow-list of analytics functions, and any optional language model only
phrases results that have already been retrieved from the analytics layer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd

from src.analytics import (
    category_performance,
    city_performance,
    churn_statistics,
    customer_segmentation,
    load_business_data,
    monthly_revenue,
    product_performance,
)
from src.database import validate_read_only_sql
from src.feature_engineering import build_customer_features
from src.ml_model import load_model


class AssistantError(ValueError):
    """Base error for invalid or unavailable assistant requests."""


class LLMResponseError(AssistantError):
    """Raised when a provider response does not match the safe contract."""


class LLMProvider(Protocol):
    """Provider interface that keeps vendor-specific code out of the assistant."""

    def generate(
        self,
        question: str,
        data: list[dict[str, Any]],
        insights: list[str],
    ) -> dict[str, Any]: ...


@dataclass
class ToolResult:
    data: list[dict[str, Any]]
    answer: str
    insights: list[str]
    recommendations: list[str]


class NullLLMProvider:
    """Explicit no-provider implementation used when LLM settings are absent."""

    def generate(
        self,
        question: str,
        data: list[dict[str, Any]],
        insights: list[str],
    ) -> dict[str, Any]:
        raise LLMResponseError("No LLM provider is configured.")


class CompatibleLLMProvider:
    """Minimal provider adapter for OpenAI-compatible JSON chat endpoints."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        question: str,
        data: list[dict[str, Any]],
        insights: list[str],
    ) -> dict[str, Any]:
        system_prompt = (
            "You are a business analyst. Use only the supplied verified data. "
            "Return JSON with answer (string), insights (array of strings), and "
            "recommendations (array of strings). Never add numbers not present in data."
        )
        request_body = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "data": data, "insights": insights},
                        default=str,
                    ),
                },
            ],
        }
        request = Request(
            self.base_url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise LLMResponseError("The configured LLM provider is unavailable.") from error

        if not isinstance(payload, dict) or not isinstance(payload.get("choices"), list) or not payload["choices"]:
            raise LLMResponseError("The LLM response did not contain choices.")
        first_choice = payload["choices"][0]
        if not isinstance(first_choice, dict) or not isinstance(first_choice.get("message"), dict):
            raise LLMResponseError("The LLM response did not contain a valid message.")
        content = first_choice["message"].get("content")
        if not isinstance(content, str):
            raise LLMResponseError("The LLM response did not contain message content.")
        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            raise LLMResponseError("The LLM response was not valid JSON.") from error


def _records(frame: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    records = frame.head(limit).to_dict(orient="records") if limit else frame.to_dict(orient="records")
    return json.loads(json.dumps(records, default=str))


def _money(value: Any) -> str:
    return f"INR {float(value):,.2f}"


def _provider_from_environment() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "none").strip().lower()
    if provider_name in {"", "none", "disabled"}:
        return NullLLMProvider()
    if provider_name in {"compatible", "openai-compatible"}:
        api_key = os.getenv("LLM_API_KEY", "").strip()
        base_url = os.getenv("LLM_BASE_URL", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()
        if not api_key or not base_url or not model:
            raise AssistantError("LLM provider configuration is incomplete.")
        return CompatibleLLMProvider(base_url, api_key, model)
    raise AssistantError(f"Unsupported LLM provider: {provider_name}")


def _validate_llm_response(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise LLMResponseError("The LLM response must be a JSON object.")
    answer = response.get("answer")
    insights = response.get("insights", [])
    recommendations = response.get("recommendations", [])
    if not isinstance(answer, str) or not answer.strip():
        raise LLMResponseError("The LLM response must contain a non-empty answer.")
    if not isinstance(insights, list) or not all(isinstance(item, str) for item in insights):
        raise LLMResponseError("LLM insights must be an array of strings.")
    if not isinstance(recommendations, list) or not all(isinstance(item, str) for item in recommendations):
        raise LLMResponseError("LLM recommendations must be an array of strings.")
    return {
        "answer": answer.strip(),
        "insights": insights,
        "recommendations": recommendations,
    }


class BusinessAssistant:
    """Route questions to verified analytics and compose safe responses."""

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or _provider_from_environment()

    def ask(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            raise AssistantError("Question must be a non-empty string.")
        question = question.strip()
        result = self._run_approved_tool(question)
        response: dict[str, Any] = {
            "question": question,
            "answer": result.answer,
            "data": result.data,
            "insights": result.insights,
            "recommendations": result.recommendations,
        }
        if result.data:
            try:
                _validate_llm_response(
                    self.provider.generate(question, result.data, result.insights)
                )
            except LLMResponseError:
                # Keep deterministic output when a provider is unavailable or malformed.
                pass
        return response

    def _run_approved_tool(self, question: str) -> ToolResult:
        normalized = question.lower()
        data = load_business_data()

        if any(term in normalized for term in ("why did revenue decrease", "revenue decrease", "revenue declined")):
            return self._revenue_change(data)
        if "last month" in normalized and "revenue" in normalized:
            return self._last_month_revenue(data)
        if "top 10" in normalized and "product" in normalized:
            return self._top_products(data)
        if "category" in normalized and any(term in normalized for term in ("most", "highest", "top")):
            return self._top_category(data)
        if "city" in normalized and any(term in normalized for term in ("most", "highest", "top")):
            return self._top_city(data)
        if "churn" in normalized and any(term in normalized for term in ("how many", "number", "percentage", "percent")):
            return self._churn_count(data)
        if "high risk" in normalized and "churn" in normalized:
            return self._high_risk_customers(data)
        if "factor" in normalized and "churn" in normalized:
            return self._churn_factors(data)
        return ToolResult(
            data=[],
            answer="The requested information is unavailable from the approved business analytics tools.",
            insights=[],
            recommendations=[],
        )

    def _last_month_revenue(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        trend = monthly_revenue(data["orders"])
        if trend.empty:
            return ToolResult([], "Revenue information is unavailable.", [], [])
        latest = trend.iloc[-1]
        record = {"month": latest["month"], "total_revenue": float(latest["total_revenue"])}
        return ToolResult(
            data=[record],
            answer=f"Revenue in the latest available month ({record['month']}) was {_money(record['total_revenue'])}.",
            insights=["The period is based on the latest month present in the business dataset."],
            recommendations=[],
        )

    def _revenue_change(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        trend = monthly_revenue(data["orders"])
        if len(trend) < 2:
            return ToolResult([], "Revenue change information is unavailable because two periods are required.", [], [])
        previous, latest = trend.iloc[-2], trend.iloc[-1]
        previous_value, latest_value = float(previous["total_revenue"]), float(latest["total_revenue"])
        change = latest_value - previous_value
        percentage = (change / previous_value * 100) if previous_value else 0
        direction = "decreased" if change < 0 else "increased"
        return ToolResult(
            data=[
                {"month": previous["month"], "total_revenue": previous_value},
                {"month": latest["month"], "total_revenue": latest_value},
            ],
            answer=f"Revenue {direction} by {_money(abs(change))} ({abs(percentage):.2f}%) from {previous['month']} to {latest['month']}.",
            insights=["This comparison uses the two latest available monthly revenue records."],
            recommendations=["Review category, product, and city performance for the same periods before taking action."],
        )

    def _top_category(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        result = category_performance(data["products"], data["order_items"])
        top = result.iloc[0]
        records = _records(result.head(10))
        return ToolResult(records, f"{top['category']} generated the most revenue at {_money(top['revenue'])}.", ["Categories are ranked by recorded line-item revenue."], ["Use the category ranking to focus assortment and campaign reviews."])

    def _top_city(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        result = city_performance(data["customers"], data["orders"])
        top = result.iloc[0]
        records = _records(result.head(10))
        return ToolResult(records, f"{top['city']} has the highest recorded sales at {_money(top['revenue'])}.", ["Cities are ranked by order revenue."], ["Compare customer counts and order volume before reallocating regional investment."])

    def _top_products(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        result = product_performance(data["products"], data["order_items"])
        records = _records(result.head(10))
        names = ", ".join(str(item["product_name"]) for item in records[:3])
        return ToolResult(records, f"The top product by recorded revenue is {names.split(', ')[0]}; the response includes the top 10 products.", ["Products are ranked by line-item revenue."], ["Review the full top-10 list for cross-sell and inventory decisions."])

    def _churn_count(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        stats = churn_statistics(data["customers"])
        record = {"total_customers": stats["total_customers"], "churned_customers": stats["churned_customers"], "churn_rate_percent": stats["churn_rate_percent"]}
        return ToolResult([record], f"{record['churned_customers']:,} of {record['total_customers']:,} customers have churned, a rate of {record['churn_rate_percent']:.2f}%.", ["Churn statistics use the recorded churn target in the customer dataset."], ["Prioritize retention analysis by city and customer segment."])

    def _high_risk_customers(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        features = build_customer_features(data["customers"], data["orders"], data["order_items"], data["products"])
        model = load_model()
        probabilities = model.predict_proba(features)
        result = features[["customer_id", "city", "segment"]].copy()
        result["churn_probability"] = probabilities
        result["risk_level"] = [
            "Low" if probability < model.risk_thresholds["Low"]
            else "Medium" if probability < model.risk_thresholds["High"]
            else "High"
            for probability in probabilities
        ]
        high_risk = result[result["risk_level"] == "High"].sort_values("churn_probability", ascending=False).head(10)
        records = _records(high_risk)
        return ToolResult(records, f"The model identified {len(high_risk):,} highest-risk customers in the top 10 returned records.", ["Risk is based on the saved churn model and current customer features."], ["Review the returned customer IDs with the retention team before outreach."])

    def _churn_factors(self, data: dict[str, pd.DataFrame]) -> ToolResult:
        customers = data["customers"]
        numeric = ["age", "tenure_months", "monthly_spend", "support_calls", "purchase_frequency"]
        rows = []
        for field in numeric:
            correlation = customers[field].corr(customers["churn"])
            rows.append({"factor": field, "churn_correlation": round(float(correlation), 4)})
        result = sorted(rows, key=lambda row: abs(row["churn_correlation"]), reverse=True)
        return ToolResult(result, "The strongest measured numeric associations with churn are shown in the data, ranked by absolute correlation.", ["Correlation indicates association, not causation."], ["Validate the strongest associations with controlled retention experiments."])


def ask_business_question(question: str, provider: LLMProvider | None = None) -> dict[str, Any]:
    return BusinessAssistant(provider=provider).ask(question)


__all__ = [
    "AssistantError",
    "BusinessAssistant",
    "CompatibleLLMProvider",
    "LLMResponseError",
    "NullLLMProvider",
    "ask_business_question",
    "validate_read_only_sql",
]
