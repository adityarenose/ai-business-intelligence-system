"""Generate realistic synthetic e-commerce data for the BI and ML project.

This module creates reproducible CSV datasets for customers, products, orders,
and order items. It is intentionally structured so that it can produce both a
full analytical dataset and a smaller sample dataset for development work.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


INDIAN_CITIES = [
    "Mumbai",
    "Delhi",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
    "Nagpur",
    "Coimbatore",
    "Visakhapatnam",
    "Patna",
    "Bhopal",
    "Indore",
    "Guwahati",
    "Thiruvananthapuram",
    "Kanpur",
    "Surat",
    "Vadodara",
    "Mysuru",
    "Noida",
    "Ghaziabad",
]

CITY_WEIGHTS = np.array(
    [
        0.16,
        0.14,
        0.12,
        0.09,
        0.08,
        0.06,
        0.06,
        0.05,
        0.04,
        0.04,
        0.03,
        0.03,
        0.03,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
    ]
)

CITY_WEIGHTS = CITY_WEIGHTS / CITY_WEIGHTS.sum()

CATEGORY_PRODUCT_NAMES = {
    "Electronics": [
        "Smartphone",
        "Laptop",
        "Wireless Earbuds",
        "Smartwatch",
        "Monitor",
        "Keyboard",
        "Mouse",
        "USB Hub",
        "Tablet",
        "Power Bank",
    ],
    "Fashion": [
        "Cotton Shirt",
        "Denim Jeans",
        "Sneakers",
        "Leather Belt",
        "Formal Jacket",
        "Saree",
        "Kurta",
        "Handbag",
        "Running Shoes",
        "Wrist Watch",
    ],
    "Home": [
        "Dining Set",
        "Table Lamp",
        "Ceiling Fan",
        "Air Purifier",
        "Vacuum Cleaner",
        "Coffee Maker",
        "Luggage Set",
        "Storage Box",
        "Mattress",
        "Cookware Set",
    ],
    "Groceries": [
        "Rice Bag",
        "Cooking Oil",
        "Organic Tea",
        "Whole Wheat Flour",
        "Spices Pack",
        "Coffee Beans",
        "Snacks Box",
        "Basmati Rice",
        "Fruit Basket",
        "Milk Pack",
    ],
    "Health": [
        "Vitamin C Tablets",
        "Protein Powder",
        "Yoga Mat",
        "Fitness Band",
        "Thermos Bottle",
        "Hand Sanitizer",
        "Face Mask Pack",
        "Hair Oil",
        "First Aid Kit",
        "Water Bottle",
    ],
    "Books": [
        "Business Strategy",
        "Python Guide",
        "History Atlas",
        "Cooking Book",
        "Science Fiction",
        "Startup Manual",
        "Self Help Guide",
        "Children Story Book",
        "Marketing Playbook",
        "Travel Journal",
    ],
    "Beauty": [
        "Face Serum",
        "Lipstick Kit",
        "Hair Dryer",
        "Perfume Set",
        "Skin Cream",
        "Makeup Brush",
        "Nail Kit",
        "Sunscreen SPF",
        "Body Lotion",
        "Essential Oil",
    ],
    "Sports": [
        "Yoga Block",
        "Cricket Bat",
        "Football",
        "Gym Dumbbells",
        "Badminton Set",
        "Cycling Helmet",
        "Hiking Backpack",
        "Skipping Rope",
        "Treadmill Mat",
        "Training Gloves",
    ],
}

CATEGORY_PRICE_RANGES = {
    "Electronics": (450.0, 2500.0),
    "Fashion": (220.0, 1600.0),
    "Home": (180.0, 1400.0),
    "Groceries": (35.0, 420.0),
    "Health": (120.0, 850.0),
    "Books": (100.0, 700.0),
    "Beauty": (150.0, 900.0),
    "Sports": (250.0, 1100.0),
}

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet", "Cash on Delivery"]


@dataclass
class DatasetConfig:
    customers: int = 12000
    products: int = 75
    seed: int = 42
    output_dir: Path | None = None
    sample_customers: int = 500
    sample_products: int = 20
    sample_output_dir: Path | None = None


def sigmoid(x: float | np.ndarray) -> float | np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def make_paths(base_dir: Path | None) -> Path:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    return base_dir


def generate_products(num_products: int, rng: np.random.Generator) -> pd.DataFrame:
    categories = list(CATEGORY_PRODUCT_NAMES.keys())
    category_cycle = [categories[i % len(categories)] for i in range(num_products)]
    product_records: list[dict[str, Any]] = []

    for product_id, category in enumerate(category_cycle, start=1):
        product_names = CATEGORY_PRODUCT_NAMES[category]
        product_name = product_names[(product_id - 1) % len(product_names)]
        if num_products > len(product_names) * len(categories):
            product_name = f"{product_name} {((product_id - 1) // len(product_names)) + 1}"

        low, high = CATEGORY_PRICE_RANGES[category]
        unit_price = round(float(rng.uniform(low, high)), 2)

        product_records.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "unit_price": unit_price,
            }
        )

    products_df = pd.DataFrame(product_records)
    return products_df


def generate_customers(num_customers: int, rng: np.random.Generator) -> pd.DataFrame:
    city_choices = rng.choice(INDIAN_CITIES, size=num_customers, p=CITY_WEIGHTS)
    genders = rng.choice(["Male", "Female", "Other"], size=num_customers, p=[0.49, 0.49, 0.02])
    ages = np.clip(rng.normal(35.0, 12.0, num_customers), 18, 78).round().astype(int)

    tenure_months = np.clip(rng.normal(30.0, 18.0, num_customers), 3, 180).round().astype(int)
    monthly_spend = np.clip(
        rng.lognormal(mean=6.7, sigma=0.8, size=num_customers),
        150,
        12000,
    )
    monthly_spend = np.round(monthly_spend, 2)

    support_calls = np.clip(
        rng.poisson(1.5, size=num_customers)
        + rng.poisson(1.0, size=num_customers) * np.where(tenure_months < 12, 1, 0),
        0,
        None,
    )

    purchase_frequency = np.clip(
        rng.gamma(shape=2.2, scale=2.7, size=num_customers),
        0.2,
        20,
    )
    purchase_frequency = np.round(purchase_frequency, 2)

    city_spend_shift = np.array(
        [
            1.05 if city == "Mumbai" else 1.0 if city == "Delhi" else 0.98 if city == "Bengaluru" else 0.96
            for city in city_choices
        ],
        dtype=float,
    )
    monthly_spend = np.round(monthly_spend * city_spend_shift, 2)

    churn_logits = (
        -2.15
        + 0.018 * support_calls
        + 0.013 * np.maximum(0, 24 - tenure_months / 2.0)
        + 0.010 * np.maximum(0, 8 - purchase_frequency)
        + 0.0008 * np.maximum(0, 1500 - monthly_spend)
        - 0.0015 * monthly_spend
    )
    churn_prob = sigmoid(churn_logits)
    churn_prob = np.clip(churn_prob, 0.04, 0.45)
    churn = rng.binomial(1, churn_prob).astype(int)

    customers_df = pd.DataFrame(
        {
            "customer_id": np.arange(1, num_customers + 1),
            "age": ages,
            "gender": genders,
            "city": city_choices,
            "tenure_months": tenure_months,
            "monthly_spend": monthly_spend,
            "support_calls": support_calls,
            "purchase_frequency": purchase_frequency,
            "churn": churn,
        }
    )

    return customers_df


def generate_order_dates_for_customer(tenure_months: int, purchase_frequency: float, rng: np.random.Generator) -> list[pd.Timestamp]:
    today = pd.Timestamp("2025-12-31")
    tenure_days = max(30, int(tenure_months * 30.4375))
    start_date = today - pd.Timedelta(days=tenure_days)
    if purchase_frequency <= 0.5:
        num_orders = int(rng.integers(1, 3))
    else:
        target_orders = int(np.clip(np.round(purchase_frequency * (tenure_months / 12.0) * rng.uniform(0.7, 1.3)), 1, 48))
        num_orders = max(1, target_orders)

    if num_orders == 1:
        return [start_date + pd.Timedelta(days=int(rng.integers(0, max(1, tenure_days + 1))))]

    candidate_dates = pd.date_range(start=start_date, end=today, freq="D")
    sampled = rng.choice(candidate_dates, size=num_orders, replace=True)
    return sorted(pd.to_datetime(sampled).tolist())


def generate_orders_and_items(
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    orders_rows: list[dict[str, Any]] = []
    order_items_rows: list[dict[str, Any]] = []

    product_ids = products_df["product_id"].tolist()
    product_prices = products_df.set_index("product_id")["unit_price"].to_dict()

    order_id_counter = 1
    item_id_counter = 1

    for _, customer in customers_df.iterrows():
        customer_id = int(customer["customer_id"])
        order_dates = generate_order_dates_for_customer(
            int(customer["tenure_months"]),
            float(customer["purchase_frequency"]),
            rng,
        )

        for order_date in order_dates:
            payment_method = rng.choice(PAYMENT_METHODS)
            item_count = int(rng.integers(1, 5))
            item_total = 0.0

            for _ in range(item_count):
                product_id = int(rng.choice(product_ids))
                quantity = int(np.clip(rng.poisson(1.8) + 1, 1, 6))
                base_price = float(product_prices[product_id])
                variation = rng.uniform(0.9, 1.25)
                unit_price = round(base_price * variation, 2)
                line_total = round(quantity * unit_price, 2)
                item_total += line_total

                order_items_rows.append(
                    {
                        "order_item_id": item_id_counter,
                        "order_id": order_id_counter,
                        "product_id": product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )
                item_id_counter += 1

            total_amount = round(item_total, 2)
            orders_rows.append(
                {
                    "order_id": order_id_counter,
                    "customer_id": customer_id,
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "total_amount": total_amount,
                    "payment_method": payment_method,
                }
            )
            order_id_counter += 1

    orders_df = pd.DataFrame(orders_rows)
    order_items_df = pd.DataFrame(order_items_rows)
    return orders_df, order_items_df


def validate_dataset(
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    results["customers_rows"] = len(customers_df)
    results["products_rows"] = len(products_df)
    results["orders_rows"] = len(orders_df)
    results["order_items_rows"] = len(order_items_df)

    results["customer_missing_values"] = int(customers_df.isna().sum().sum())
    results["product_missing_values"] = int(products_df.isna().sum().sum())
    results["orders_missing_values"] = int(orders_df.isna().sum().sum())
    results["order_items_missing_values"] = int(order_items_df.isna().sum().sum())

    results["customer_duplicate_ids"] = int(customers_df["customer_id"].duplicated().sum())
    results["product_duplicate_ids"] = int(products_df["product_id"].duplicated().sum())
    results["order_duplicate_ids"] = int(orders_df["order_id"].duplicated().sum())
    results["order_item_duplicate_ids"] = int(order_items_df["order_item_id"].duplicated().sum())

    invalid_customer_orders = set(orders_df[~orders_df["customer_id"].isin(customers_df["customer_id"])].index)
    invalid_order_items = set(
        order_items_df[~order_items_df["order_id"].isin(orders_df["order_id"])].index
    )
    invalid_products = set(
        order_items_df[~order_items_df["product_id"].isin(products_df["product_id"])].index
    )

    results["invalid_customer_orders"] = len(invalid_customer_orders)
    results["invalid_order_items"] = len(invalid_order_items)
    results["invalid_products"] = len(invalid_products)

    churn_distribution = customers_df["churn"].value_counts(normalize=True).sort_index()
    results["churn_distribution"] = {str(int(k)): round(float(v), 4) for k, v in churn_distribution.items()}

    results["customer_summary"] = {
        "age_mean": round(float(customers_df["age"].mean()), 2),
        "spend_mean": round(float(customers_df["monthly_spend"].mean()), 2),
        "spend_p95": round(float(customers_df["monthly_spend"].quantile(0.95)), 2),
        "support_calls_mean": round(float(customers_df["support_calls"].mean()), 2),
        "purchase_frequency_mean": round(float(customers_df["purchase_frequency"].mean()), 2),
    }

    results["orders_summary"] = {
        "total_amount_mean": round(float(orders_df["total_amount"].mean()), 2),
        "total_amount_max": round(float(orders_df["total_amount"].max()), 2),
        "payment_methods": orders_df["payment_method"].value_counts().to_dict(),
    }

    return results


def save_csvs(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def generate_dataset(config: DatasetConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(config.seed)

    customers_df = generate_customers(config.customers, rng)
    products_df = generate_products(config.products, rng)
    orders_df, order_items_df = generate_orders_and_items(customers_df, products_df, rng)

    validation = validate_dataset(customers_df, products_df, orders_df, order_items_df)
    if validation["customer_duplicate_ids"] or validation["product_duplicate_ids"] or validation["order_duplicate_ids"] or validation["order_item_duplicate_ids"]:
        raise ValueError("Duplicate IDs detected in generated dataset.")
    if validation["customer_missing_values"] or validation["product_missing_values"] or validation["orders_missing_values"] or validation["order_items_missing_values"]:
        raise ValueError("Missing values detected in generated dataset.")
    if validation["invalid_customer_orders"] or validation["invalid_order_items"] or validation["invalid_products"]:
        raise ValueError("Invalid foreign-key relationships detected in generated dataset.")

    output_dir = make_paths(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_csvs(customers_df, output_dir / "customers.csv")
    save_csvs(products_df, output_dir / "products.csv")
    save_csvs(orders_df, output_dir / "orders.csv")
    save_csvs(order_items_df, output_dir / "order_items.csv")

    return customers_df, products_df, orders_df, order_items_df


def generate_sample_dataset(config: DatasetConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sample_config = DatasetConfig(
        customers=config.sample_customers,
        products=config.sample_products,
        seed=config.seed + 1,
        output_dir=config.sample_output_dir,
    )
    return generate_dataset(sample_config)


def parse_args() -> DatasetConfig:
    root_dir = Path(__file__).resolve().parents[1]
    default_raw = root_dir / "data" / "raw"
    default_sample = root_dir / "data" / "sample"

    parser = argparse.ArgumentParser(description="Generate realistic synthetic business e-commerce dataset.")
    parser.add_argument("--customers", type=int, default=12000, help="Number of customers to generate.")
    parser.add_argument("--products", type=int, default=75, help="Number of products to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output-dir", type=Path, default=default_raw, help="Directory for full CSV outputs.")
    parser.add_argument("--sample-customers", type=int, default=500, help="Number of customers in sample dataset.")
    parser.add_argument("--sample-products", type=int, default=20, help="Number of products in sample dataset.")
    parser.add_argument("--sample-output-dir", type=Path, default=default_sample, help="Directory for sample CSV outputs.")
    args = parser.parse_args()

    return DatasetConfig(
        customers=args.customers,
        products=args.products,
        seed=args.seed,
        output_dir=args.output_dir,
        sample_customers=args.sample_customers,
        sample_products=args.sample_products,
        sample_output_dir=args.sample_output_dir,
    )


def main() -> None:
    config = parse_args()
    full_customers, full_products, full_orders, full_order_items = generate_dataset(config)
    sample_customers, sample_products, sample_orders, sample_order_items = generate_sample_dataset(config)

    validation = validate_dataset(full_customers, full_products, full_orders, full_order_items)
    print("Full dataset summary:")
    print(f"Customers: {validation['customers_rows']}")
    print(f"Products: {validation['products_rows']}")
    print(f"Orders: {validation['orders_rows']}")
    print(f"Order items: {validation['order_items_rows']}")
    print(f"Customer missing values: {validation['customer_missing_values']}")
    print(f"Order missing values: {validation['orders_missing_values']}")
    print(f"Duplicate customer IDs: {validation['customer_duplicate_ids']}")
    print(f"Invalid customer orders: {validation['invalid_customer_orders']}")
    print(f"Invalid product references: {validation['invalid_products']}")
    print(f"Churn distribution: {validation['churn_distribution']}")
    print(f"Customer statistics: {validation['customer_summary']}")

    print("\nSample dataset summary:")
    sample_validation = validate_dataset(sample_customers, sample_products, sample_orders, sample_order_items)
    print(f"Customers: {sample_validation['customers_rows']}")
    print(f"Products: {sample_validation['products_rows']}")
    print(f"Orders: {sample_validation['orders_rows']}")
    print(f"Order items: {sample_validation['order_items_rows']}")


if __name__ == "__main__":
    main()
