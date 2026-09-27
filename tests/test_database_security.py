import pandas as pd
import pytest

from src.database import load_csv_to_table, validate_read_only_sql


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers INTO OUTFILE 'export.csv'",
        "SELECT * FROM customers INTO DUMPFILE 'export.bin'",
        "SELECT * FROM customers; DROP TABLE customers",
        "SELECT * FROM customers -- hide a second operation",
    ],
)
def test_read_only_sql_rejects_file_writes_and_stacked_or_commented_queries(query):
    with pytest.raises(ValueError):
        validate_read_only_sql(query)


def test_csv_import_rejects_unknown_identifier_before_connecting(tmp_path):
    csv_path = tmp_path / "customers.csv"
    pd.DataFrame({"customer_id": [1], "unexpected": ["value"]}).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Unsupported columns"):
        load_csv_to_table(csv_path, "customers")

    with pytest.raises(ValueError, match="Unsupported import table"):
        load_csv_to_table(csv_path, "customers; DROP TABLE customers")