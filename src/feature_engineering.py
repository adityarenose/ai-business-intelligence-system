"""Feature engineering for customer churn prediction.

This module builds a customer-level dataset from the business tables and prepares
clean features for model training and inference.
"""

from __future__ import annotations

import pandas as pd

from src.analytics import customer_segmentation


def prepare_customer_dataset(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create a customer-level feature table ready for churn modeling."""
    # Exclude the target-derived churn signal from model features.
    segment_df = customer_segmentation(
        customers_df=customers_df,
        orders_df=orders_df,
        use_churn_signal=False,
    )
    orders_by_customer = orders_df.groupby("customer_id").agg(
        total_orders=("order_id", "count"),
        total_spent=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
    )
    orders_by_customer = orders_by_customer.reset_index()

    feature_df = customers_df.merge(orders_by_customer, on="customer_id", how="left")
    feature_df = feature_df.merge(
        segment_df[["customer_id", "segment"]], on="customer_id", how="left"
    )

    feature_df["total_orders"] = feature_df["total_orders"].fillna(0).astype(int)
    feature_df["total_spent"] = feature_df["total_spent"].fillna(0).round(2)
    feature_df["avg_order_value"] = feature_df["avg_order_value"].fillna(0).round(2)
    feature_df["segment"] = feature_df["segment"].fillna("Low Value")

    if "payment_method" not in feature_df.columns:
        if orders_df is not None and not orders_df.empty:
            payment_method_map = (
                orders_df.groupby("customer_id")["payment_method"].agg(lambda s: s.mode().iloc[0] if len(s.mode()) else s.iloc[0])
            ).reset_index()
            feature_df = feature_df.merge(payment_method_map, on="customer_id", how="left")
        else:
            feature_df["payment_method"] = "UPI"

    feature_df["monthly_spend"] = feature_df["monthly_spend"].fillna(0)
    feature_df["purchase_frequency"] = feature_df["purchase_frequency"].fillna(0)
    feature_df["support_calls"] = feature_df["support_calls"].fillna(0)
    feature_df["tenure_months"] = feature_df["tenure_months"].fillna(0).astype(int)
    feature_df["churn"] = feature_df["churn"].astype(int)

    return feature_df


def build_customer_features(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Construct feature-ready churn dataset with the target column included."""
    data = prepare_customer_dataset(customers_df, orders_df, order_items_df, products_df)
    return data


def select_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return the churn model feature columns."""
    target_columns = {"customer_id", "churn"}
    exclude = {"created_at"}
    return [col for col in df.columns if col not in target_columns and col not in exclude]


def get_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Return X, y and feature list for model training."""
    feature_cols = select_feature_columns(df)
    X = df[feature_cols].copy()
    y = df["churn"].astype(int)
    return X, y, feature_cols


if __name__ == "__main__":
    from src.analytics import load_business_data

    data = load_business_data()
    df = build_customer_features(
        customers_df=data["customers"],
        orders_df=data["orders"],
        order_items_df=data["order_items"],
        products_df=data["products"],
    )
    print(df.head())
    print(df.columns.tolist())
