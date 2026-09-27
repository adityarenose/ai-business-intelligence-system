"""Database access utilities for the BI system.

This module centralizes MySQL configuration, connection handling, and reusable
queries for analytics and data loading. Values are loaded from environment
variables rather than hardcoded secrets.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FORBIDDEN_SQL = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC(?:UTE)?)\b",
    re.IGNORECASE,
)
IMPORT_COLUMNS = {
    "customers": {"customer_id", "age", "gender", "city", "tenure_months", "monthly_spend", "support_calls", "purchase_frequency", "churn"},
    "products": {"product_id", "product_name", "category", "unit_price"},
    "orders": {"order_id", "customer_id", "order_date", "total_amount", "payment_method"},
    "order_items": {"order_item_id", "order_id", "product_id", "quantity", "unit_price", "line_total"},
}


def validate_read_only_sql(query: str) -> str:
    """Allow only one plain SELECT statement for read-only reporting."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("SQL query cannot be empty.")
    normalized = query.strip()
    if not re.match(r"^SELECT\b", normalized, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    if FORBIDDEN_SQL.search(normalized):
        raise ValueError("The query contains a forbidden SQL operation.")
    if ";" in normalized.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed.")
    if "--" in normalized or "/*" in normalized or "*/" in normalized:
        raise ValueError("SQL comments are not allowed.")
    if re.search(r"\bINTO\s+(?:OUTFILE|DUMPFILE)\b", normalized, re.IGNORECASE):
        raise ValueError("File-writing SELECT queries are not allowed.")
    return normalized


def _split_sql_statements(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for character in script:
        if quote:
            current.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"'", '"', "`"}:
            quote = character
            current.append(character)
        elif character == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(character)
    final_statement = "".join(current).strip()
    if final_statement:
        statements.append(final_statement)
    return statements


def get_db_config() -> dict[str, str]:
    """Return MySQL configuration from environment variables."""
    database_url = os.getenv("DATABASE_URL", "")
    parsed_url = urlparse(database_url) if database_url else None
    return {
        "host": os.getenv("DB_HOST") or (parsed_url.hostname if parsed_url else None) or "localhost",
        "port": int(os.getenv("DB_PORT") or (parsed_url.port if parsed_url else None) or 3306),
        "user": os.getenv("DB_USER") or (unquote(parsed_url.username) if parsed_url and parsed_url.username else None) or "root",
        "password": os.getenv("DB_PASSWORD") or (unquote(parsed_url.password) if parsed_url and parsed_url.password else None) or "",
        "database": os.getenv("DB_NAME") or (parsed_url.path.lstrip("/") if parsed_url and parsed_url.path else None) or "ai_bi_system",
        "autocommit": True,
        "charset": "utf8mb4",
    }


def get_connection():
    """Create a connection to the configured MySQL database."""
    config = get_db_config()
    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        autocommit=config["autocommit"],
        charset=config["charset"],
    )


def read_sql_file(file_path: str | Path) -> str:
    """Read SQL file content as a string."""
    return Path(file_path).read_text(encoding="utf-8")


def execute_sql_script(sql_path: str | Path) -> None:
    """Execute a SQL script against the configured database."""
    script = read_sql_file(sql_path)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for statement in _split_sql_statements(script):
                cursor.execute(statement)
    finally:
        connection.close()


def load_csv_to_table(csv_path: str | Path, table_name: str, database_name: str | None = None) -> None:
    """Load a CSV file into a MySQL table using pandas and a parameterized insert strategy.

    This is a reliable import path when the local MySQL environment is not configured to use
    MySQL's LOAD DATA INFILE with the exact Windows file paths used by the project.
    """
    df = pd.read_csv(csv_path)
    if table_name not in IMPORT_COLUMNS:
        raise ValueError(f"Unsupported import table: {table_name}")
    if not set(df.columns).issubset(IMPORT_COLUMNS[table_name]):
        raise ValueError(f"Unsupported columns for import table: {table_name}")
    if database_name is not None:
        configured_database = get_db_config()["database"]
        if database_name != configured_database:
            raise ValueError("Import database must match the configured database.")
        table_name = f"`{database_name}`.`{table_name}`"
    else:
        table_name = f"`{table_name}`"

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(df.columns))
            column_names = ", ".join(f"`{column}`" for column in df.columns)
            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            cursor.executemany(insert_sql, list(df.itertuples(index=False, name=None)))
    finally:
        connection.close()


def execute_query(query: str, params: tuple[Any, ...] | None = None) -> list[tuple[Any, ...]]:
    """Run a SQL query with optional parameter binding."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()


def fetch_one(query: str, params: tuple[Any, ...] | None = None) -> tuple[Any, ...] | None:
    """Return a single row from a query result."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            result = cursor.fetchone()
            return result
    finally:
        connection.close()


def test_connection() -> dict[str, Any]:
    """Test the database connection and return basic metadata."""
    result = fetch_one("SELECT DATABASE() AS current_db, VERSION() AS version")
    return {
        "current_db": result[0] if result else None,
        "version": result[1] if result else None,
    }


if __name__ == "__main__":
    print(test_connection())
