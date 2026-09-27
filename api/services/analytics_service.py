"""Service functions that adapt the analytics layer for API responses."""

from __future__ import annotations

from typing import Any

from src.analytics import (
    business_summary,
    category_performance,
    city_performance,
    churn_statistics,
    customer_segmentation,
    load_business_data,
    monthly_revenue,
    product_performance,
)


def _records(frame: Any) -> list[dict[str, Any]]:
    """Convert an analytics DataFrame to JSON-compatible records."""
    return frame.to_dict(orient="records")


def get_summary() -> dict[str, Any]:
    return business_summary()


def get_sales_trend() -> list[dict[str, Any]]:
    data = load_business_data()
    return _records(monthly_revenue(orders_df=data["orders"]))


def get_category_sales() -> list[dict[str, Any]]:
    data = load_business_data()
    return _records(
        category_performance(
            products_df=data["products"], order_items_df=data["order_items"]
        )
    )


def get_product_sales() -> list[dict[str, Any]]:
    data = load_business_data()
    return _records(
        product_performance(
            products_df=data["products"], order_items_df=data["order_items"]
        )
    )


def get_city_sales() -> list[dict[str, Any]]:
    data = load_business_data()
    return _records(
        city_performance(customers_df=data["customers"], orders_df=data["orders"])
    )


def get_customer_segments() -> dict[str, int]:
    data = load_business_data()
    segments = customer_segmentation(
        customers_df=data["customers"], orders_df=data["orders"]
    )
    return {str(key): int(value) for key, value in segments["segment"].value_counts().items()}


def get_churn_statistics() -> dict[str, Any]:
    data = load_business_data()
    return churn_statistics(customers_df=data["customers"])
