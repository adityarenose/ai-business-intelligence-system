"""Reusable analytics functions for the business intelligence project.

The module provides clean, structured outputs for KPIs and business analysis.
It reads from the generated CSV data by default and can optionally query a MySQL
instance when configured through the project database layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database import execute_query, get_connection, validate_read_only_sql

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_business_data(data_dir: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the generated raw datasets into memory.

    Returns a dictionary containing the Customer, Product, Order, and Order Item
    tables required for downstream analytics.
    """
    base_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    required_files = {
        "customers": base_dir / "customers.csv",
        "products": base_dir / "products.csv",
        "orders": base_dir / "orders.csv",
        "order_items": base_dir / "order_items.csv",
    }

    missing = [name for name, path in required_files.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required data files: {', '.join(missing)}")

    return {
        "customers": pd.read_csv(required_files["customers"]),
        "products": pd.read_csv(required_files["products"]),
        "orders": pd.read_csv(required_files["orders"]),
        "order_items": pd.read_csv(required_files["order_items"]),
    }


def total_revenue(orders_df: pd.DataFrame | None = None, order_items_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> float:
    """Return total revenue across all orders."""
    if orders_df is None or order_items_df is None:
        data = load_business_data(data_dir)
        orders_df = data["orders"]
        order_items_df = data["order_items"]

    if "line_total" in order_items_df.columns:
        return round(float(order_items_df["line_total"].sum()), 2)
    return round(float(orders_df["total_amount"].sum()), 2)


def total_orders(orders_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> int:
    """Return the total number of orders."""
    if orders_df is None:
        orders_df = load_business_data(data_dir)["orders"]
    return int(orders_df.shape[0])


def total_customers(customers_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> int:
    """Return the total number of customers."""
    if customers_df is None:
        customers_df = load_business_data(data_dir)["customers"]
    return int(customers_df.shape[0])


def average_order_value(orders_df: pd.DataFrame | None = None, order_items_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> float:
    """Return average order value."""
    if orders_df is None or order_items_df is None:
        data = load_business_data(data_dir)
        orders_df = data["orders"]
        order_items_df = data["order_items"]

    orders_count = total_orders(orders_df)
    if orders_count == 0:
        return 0.0

    revenue = total_revenue(orders_df, order_items_df)
    return round(float(revenue / orders_count), 2)


def monthly_revenue(orders_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return monthly revenue totals as a clean table for dashboards.

    Returns columns: month, total_revenue.
    """
    if orders_df is None:
        orders_df = load_business_data(data_dir)["orders"]

    month_df = orders_df.copy()
    month_df["order_date"] = pd.to_datetime(month_df["order_date"]) 
    month_df["month"] = month_df["order_date"].dt.to_period("M").astype(str)

    result = (
        month_df.groupby("month", as_index=False)["total_amount"]
        .sum()
        .rename(columns={"total_amount": "total_revenue"})
    )
    result["total_revenue"] = result["total_revenue"].round(2)
    return result.sort_values("month").reset_index(drop=True)


def category_performance(products_df: pd.DataFrame | None = None, order_items_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return revenue and units sold by product category."""
    if products_df is None or order_items_df is None:
        data = load_business_data(data_dir)
        products_df = data["products"]
        order_items_df = data["order_items"]

    merged = order_items_df.merge(products_df[["product_id", "category"]], on="product_id", how="left")
    result = (
        merged.groupby("category", as_index=False)
        .agg(revenue=("line_total", "sum"), units_sold=("quantity", "sum"), order_count=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    result["revenue"] = result["revenue"].round(2)
    return result


def product_performance(products_df: pd.DataFrame | None = None, order_items_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return revenue and units sold by product."""
    if products_df is None or order_items_df is None:
        data = load_business_data(data_dir)
        products_df = data["products"]
        order_items_df = data["order_items"]

    merged = order_items_df.merge(products_df[["product_id", "product_name", "category"]], on="product_id", how="left")
    result = (
        merged.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(revenue=("line_total", "sum"), units_sold=("quantity", "sum"), order_count=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    result["revenue"] = result["revenue"].round(2)
    return result


def city_performance(customers_df: pd.DataFrame | None = None, orders_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return revenue and order totals grouped by customer city."""
    if customers_df is None or orders_df is None:
        data = load_business_data(data_dir)
        customers_df = data["customers"]
        orders_df = data["orders"]

    merged = orders_df.merge(customers_df[["customer_id", "city"]], on="customer_id", how="left")
    result = (
        merged.groupby("city", as_index=False)
        .agg(revenue=("total_amount", "sum"), orders=("order_id", "count"), customers=("customer_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    result["revenue"] = result["revenue"].round(2)
    return result


def customer_spending(customers_df: pd.DataFrame | None = None, orders_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return customer-level total spend and order count."""
    if customers_df is None or orders_df is None:
        data = load_business_data(data_dir)
        customers_df = data["customers"]
        orders_df = data["orders"]

    merged = customers_df[["customer_id", "city", "monthly_spend", "purchase_frequency", "support_calls", "churn"]].merge(
        orders_df.groupby("customer_id", as_index=False)["total_amount"].sum(),
        on="customer_id",
        how="left",
    )
    merged = merged.rename(columns={"total_amount": "total_spent"})
    merged["total_spent"] = merged["total_spent"].fillna(0).round(2)

    order_counts = orders_df.groupby("customer_id", as_index=False)["order_id"].count().rename(columns={"order_id": "total_orders"})
    merged = merged.merge(order_counts, on="customer_id", how="left")
    merged["total_orders"] = merged["total_orders"].fillna(0).astype(int)
    return merged.sort_values("total_spent", ascending=False).reset_index(drop=True)


def customer_segmentation(
    customers_df: pd.DataFrame | None = None,
    orders_df: pd.DataFrame | None = None,
    data_dir: str | Path | None = None,
    use_churn_signal: bool = True,
) -> pd.DataFrame:
    """Assign transparent business segments based on customer value.

    Segments are created using lifetime value approximations and churn risk signals.
    """
    if customers_df is None or orders_df is None:
        data = load_business_data(data_dir)
        customers_df = data["customers"]
        orders_df = data["orders"]

    customer_value = customer_spending(customers_df, orders_df)
    seg_df = customer_value.copy()

    def segment(row: pd.Series) -> str:
        total_spent = float(row["total_spent"])
        if total_spent >= 10000 or row["monthly_spend"] >= 2500:
            return "High Value"
        if total_spent >= 4000 or row["monthly_spend"] >= 1200:
            return "Medium Value"
        if (use_churn_signal and row["churn"] == 1) or row["support_calls"] >= 5:
            return "At Risk"
        return "Low Value"

    seg_df["segment"] = seg_df.apply(segment, axis=1)
    return seg_df[["customer_id", "city", "total_spent", "total_orders", "monthly_spend", "support_calls", "churn", "segment"]]


def churn_statistics(customers_df: pd.DataFrame | None = None, data_dir: str | Path | None = None) -> dict[str, Any]:
    """Return churn KPIs and summary values for dashboard consumption."""
    if customers_df is None:
        customers_df = load_business_data(data_dir)["customers"]

    churn_rate = float(customers_df["churn"].mean() * 100)
    churn_summary = {
        "total_customers": int(customers_df.shape[0]),
        "churned_customers": int(customers_df["churn"].sum()),
        "churn_rate_percent": round(churn_rate, 2),
        "avg_support_calls": round(float(customers_df.loc[customers_df["churn"] == 1, "support_calls"].mean()), 2),
        "avg_monthly_spend": round(float(customers_df.loc[customers_df["churn"] == 1, "monthly_spend"].mean()), 2),
        "avg_tenure_months": round(float(customers_df.loc[customers_df["churn"] == 1, "tenure_months"].mean()), 2),
        "by_city": (
            customers_df.groupby("city")["churn"].mean().mul(100).round(2).sort_values(ascending=False).to_dict()
        ),
    }
    return churn_summary


def business_summary(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Return a unified summary payload suitable for an API dashboard."""
    data = load_business_data(data_dir)
    customers_df = data["customers"]
    orders_df = data["orders"]
    order_items_df = data["order_items"]
    products_df = data["products"]

    summary = {
        "total_revenue": total_revenue(orders_df=orders_df, order_items_df=order_items_df),
        "total_orders": total_orders(orders_df=orders_df),
        "total_customers": total_customers(customers_df=customers_df),
        "average_order_value": average_order_value(orders_df=orders_df, order_items_df=order_items_df),
        "monthly_revenue": monthly_revenue(orders_df=orders_df).to_dict(orient="records"),
        "category_performance": category_performance(products_df=products_df, order_items_df=order_items_df).to_dict(orient="records"),
        "product_performance": product_performance(products_df=products_df, order_items_df=order_items_df).head(10).to_dict(orient="records"),
        "city_performance": city_performance(customers_df=customers_df, orders_df=orders_df).to_dict(orient="records"),
        "customer_spending": customer_spending(customers_df=customers_df, orders_df=orders_df).head(10).to_dict(orient="records"),
        "customer_segmentation": customer_segmentation(customers_df=customers_df, orders_df=orders_df).groupby("segment").size().to_dict(),
        "churn_statistics": churn_statistics(customers_df=customers_df),
    }
    return summary


def fetch_sql_metric(query: str, params: tuple[Any, ...] | None = None) -> pd.DataFrame:
    """Execute an SQL query against MySQL and return a DataFrame.

    This is intended for later API/database-backed reporting when the database is
    configured and the MySQL connection is available.
    """
    rows = execute_query(validate_read_only_sql(query), params)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


if __name__ == "__main__":
    dataset = load_business_data()
    summary = business_summary()
    print("Summary keys:", sorted(summary.keys()))
    print("Total revenue:", summary["total_revenue"])
    print("Total orders:", summary["total_orders"])
    print("Average order value:", summary["average_order_value"])
    print("Churn rate:", summary["churn_statistics"]["churn_rate_percent"], "%")
