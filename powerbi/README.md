# Power BI Reporting Guide

This guide defines the Power BI model for the AI Business Intelligence System. The report must be connected to the project's MySQL database and must use the imported project tables. Do not type dashboard results into Power BI and do not replace the database with manually created sample values.

## 1. Prerequisites

- Windows Power BI Desktop, preferably the same architecture as the installed MySQL Connector/NET.
- MySQL Server 8.0 running locally or reachable from the workstation.
- The Oracle MySQL Connector/NET installed before opening Power BI Desktop. Install the current compatible 8.0.x connector from Oracle, then restart Power BI Desktop.
- The project database created from `database/schema.sql`.
- The CSV data loaded with `database/seed.sql`.
- A database account with read-only access for reporting.

The project defaults are documented in `.env.example`:

- Host: `localhost`
- Port: `3306`
- Database: `ai_bi_system`

Use the actual values configured in the environment. Do not expose `DB_PASSWORD` in a PBIX file, screenshot, frontend, or source repository.

## 2. Prepare MySQL

From a MySQL client, an administrator can create a dedicated read-only Power BI account. Replace the placeholder password with a secret managed outside source control:

```sql
CREATE USER 'powerbi_reader'@'localhost'
IDENTIFIED BY '<strong-password-managed-outside-the-repository>';

GRANT SELECT ON ai_bi_system.* TO 'powerbi_reader'@'localhost';
FLUSH PRIVILEGES;
```

If Power BI connects from another machine, create the account for the specific reporting host rather than using `%` where possible. The reporting account needs `SELECT` only. It does not need `INSERT`, `UPDATE`, `DELETE`, schema, user-management, or file privileges.

Confirm the database is populated before opening Power BI:

```sql
USE ai_bi_system;
SELECT COUNT(*) AS customers FROM customers;
SELECT COUNT(*) AS products FROM products;
SELECT COUNT(*) AS orders FROM orders;
SELECT COUNT(*) AS order_items FROM order_items;
```

The project seed script currently uses `LOAD DATA INFILE` paths from the local Windows workspace. Run it from an administrator-approved MySQL client when the server's `secure_file_priv` setting permits that directory. If MySQL rejects the file path, move/copy the generated CSVs to the server-approved import directory and update the import command for the local environment; do not alter the data values.

## 3. Connect Power BI Desktop

1. Start MySQL Server and confirm the configured host and port are reachable.
2. Open Power BI Desktop.
3. Select **Home > Get data > More... > Database > MySQL database**.
4. Enter the server as `localhost:3306` (or the configured host and port). Enter `ai_bi_system` as the database name.
5. Select **Import** as the data connectivity mode. Import is recommended for this project because the synthetic dataset is designed for an in-memory analytical report and the model can be refreshed from MySQL.
6. Select **Database** authentication.
7. Enter the dedicated read-only username, such as `powerbi_reader`, and its password. Do not use the application owner account or a root account.
8. In Navigator, select these four tables:
   - `customers`
   - `products`
   - `orders`
   - `order_items`
9. Choose **Load** if the column types are already correct, or choose **Transform Data** to verify types before loading.
10. In Power Query, confirm the following types:
    - IDs: whole number
    - `age`, `tenure_months`, `support_calls`, `quantity`: whole number
    - `monthly_spend`, `purchase_frequency`, `total_amount`, `unit_price`, `line_total`: decimal number/currency as appropriate
    - `order_date`: date
    - `churn`: whole number or true/false consistently
    - Text fields: text
11. Select **Close & Apply**.
12. Configure scheduled refresh only after the gateway and MySQL connection have been secured. Never embed a password in M code or a visual.

If the MySQL connector does not appear, close Power BI Desktop, install the compatible MySQL Connector/NET version, and reopen Power BI Desktop. If connection fails, verify the MySQL service, port, database name, firewall, authentication plugin, and read-only account grants.

## 4. Recommended Data Model

Use a simple star schema with two fact tables and two dimensions:

```text
DimDate[Date]       1 ─── * Orders[order_date]
DimCustomers[id]    1 ─── * Orders[customer_id]
Orders[order_id]    1 ─── * OrderItems[order_id]
DimProducts[id]     1 ─── * OrderItems[product_id]
```

### Imported tables

| Table | Role | Grain | Important columns |
| --- | --- | --- | --- |
| `customers` | Customer dimension | One row per customer | `customer_id`, `age`, `gender`, `city`, `tenure_months`, `monthly_spend`, `support_calls`, `purchase_frequency`, `churn` |
| `products` | Product dimension | One row per product | `product_id`, `product_name`, `category`, `unit_price` |
| `orders` | Order fact | One row per order | `order_id`, `customer_id`, `order_date`, `total_amount`, `payment_method` |
| `order_items` | Order-line fact | One row per order item | `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `line_total` |

Rename tables in the model to `Customers`, `Products`, `Orders`, and `OrderItems` if desired. The DAX below assumes those readable names. Either keep the original names and adjust DAX references, or rename consistently; do not mix both conventions.

### Relationships

Create these active, single-direction, one-to-many relationships:

| One side | Many side | Cross-filter direction |
| --- | --- | --- |
| `Customers[customer_id]` | `Orders[customer_id]` | Single: Customers to Orders |
| `Orders[order_id]` | `OrderItems[order_id]` | Single: Orders to OrderItems |
| `Products[product_id]` | `OrderItems[product_id]` | Single: Products to OrderItems |
| `Date[Date]` | `Orders[order_date]` | Single: Date to Orders |

Do not create a direct `Products` to `Orders` relationship. Product filtering reaches orders through `OrderItems`. Do not create bidirectional relationships unless a specific report requirement is tested; they can create ambiguous filter paths.

### Date table

Create a dedicated date table because monthly, quarterly, yearly, and prior-period analysis should not depend on text extracted from `order_date`:

```DAX
Date =
ADDCOLUMNS(
    CALENDAR(MIN(Orders[order_date]), MAX(Orders[order_date])),
    "Year", YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month", FORMAT([Date], "MMM"),
    "Year Month", FORMAT([Date], "YYYY-MM"),
    "Quarter", "Q" & FORMAT([Date], "Q")
)
```

In **Table tools**, mark `Date` as the date table using `Date[Date]`. Sort `Date[Month]` by `Date[Month Number]` and sort `Date[Year Month]` by `Date[Date]` or a numeric Year Month key if Power BI requests one.

### Calculated columns

Calculated columns are optional. Add only those that improve filtering and reproduce documented project rules:

```DAX
Customer Total Spent =
CALCULATE(
    SUM(Orders[total_amount])
)
```

The `Customers` to `Orders` relationship allows the calculated column to aggregate each customer's orders. This is a stored model value and will update on dataset refresh.

```DAX
Customer Segment =
SWITCH(
    TRUE(),
    Customers[Customer Total Spent] >= 10000 || Customers[monthly_spend] >= 2500, "High Value",
    Customers[Customer Total Spent] >= 4000 || Customers[monthly_spend] >= 1200, "Medium Value",
    Customers[churn] = 1 || Customers[support_calls] >= 5, "At Risk",
    "Low Value"
)
```

This reproduces the transparent segmentation rules in `src/analytics.py`. It is a business segment, not a machine-learning prediction.

Do not add a `High Risk` calculated column to Power BI. The saved churn model is not a MySQL table and its probability output is not available in the Power BI import. Use `Customers[churn]` for recorded churn analysis. If model predictions are later exported as a governed table, add that table and document its refresh lineage before using it in visuals.

## 5. DAX Measures

Create these measures in a dedicated measure table named `_Measures`. The measures use actual imported project data and return blank-safe values where appropriate.

### Core sales measures

```DAX
Total Revenue =
COALESCE(SUM(OrderItems[line_total]), 0)
```

```DAX
Total Orders =
DISTINCTCOUNT(Orders[order_id])
```

```DAX
Total Customers =
DISTINCTCOUNT(Customers[customer_id])
```

```DAX
Average Order Value =
DIVIDE([Total Revenue], [Total Orders], 0)
```

```DAX
Units Sold =
COALESCE(SUM(OrderItems[quantity]), 0)
```

```DAX
Average Selling Price =
DIVIDE([Total Revenue], [Units Sold], 0)
```

```DAX
Revenue Previous Month =
CALCULATE(
    [Total Revenue],
    DATEADD('Date'[Date], -1, MONTH)
)
```

```DAX
Revenue Change =
[Total Revenue] - [Revenue Previous Month]
```

```DAX
Revenue Change % =
DIVIDE([Revenue Change], [Revenue Previous Month], 0)
```

```DAX
Revenue YTD =
TOTALYTD([Total Revenue], 'Date'[Date])
```

### Customer and churn measures

```DAX
Churned Customers =
CALCULATE(
    DISTINCTCOUNT(Customers[customer_id]),
    Customers[churn] = 1
)
```

```DAX
Churn Rate =
DIVIDE([Churned Customers], [Total Customers], 0)
```

Format `Churn Rate` and `Revenue Change %` as percentages. Format revenue and average order measures as the project's currency, INR, if that is the business reporting convention.

```DAX
Average Monthly Spend =
AVERAGE(Customers[monthly_spend])
```

```DAX
Average Tenure Months =
AVERAGE(Customers[tenure_months])
```

```DAX
Average Support Calls =
AVERAGE(Customers[support_calls])
```

```DAX
At Risk Customers =
CALCULATE(
    DISTINCTCOUNT(Customers[customer_id]),
    Customers[Customer Segment] = "At Risk"
)
```

```DAX
High Value Customers =
CALCULATE(
    DISTINCTCOUNT(Customers[customer_id]),
    Customers[Customer Segment] = "High Value"
)
```

### Data quality checks

These measures are optional but useful on a model validation page or during development:

```DAX
Orders Without Customer =
COUNTROWS(
    FILTER(
        Orders,
        ISBLANK(RELATED(Customers[customer_id]))
    )
)
```

```DAX
Order Items Without Product =
COUNTROWS(
    FILTER(
        OrderItems,
        ISBLANK(RELATED(Products[product_id]))
    )
)
```

Both should be zero after a successful database load. Do not hide referential-integrity problems with `COALESCE`; fix the source load or relationship instead.

## 6. Report Pages

Use the following page layouts. Every visual must be bound to an imported field or a DAX measure. Do not type a result into a card title or text box.

### Page 1: Executive Overview

**Purpose:** Provide a concise current view of business performance and retention.

**KPI cards:**

- `[Total Revenue]`
- `[Total Orders]`
- `[Total Customers]`
- `[Average Order Value]`
- `[Churn Rate]`

**Charts and tables:**

- Line chart: `Date[Year Month]` by `[Total Revenue]`.
- Clustered bar chart: `Products[category]` by `[Total Revenue]`, sorted descending.
- Top-N bar chart: `Products[product_name]` by `[Total Revenue]`, filtered to top 10.
- Map or bar chart: `Customers[city]` by `[Total Revenue]`.
- Small table: `Date[Year Month]`, `[Total Revenue]`, `[Revenue Change %]`.

**Slicers:**

- `Date[Year]`
- `Date[Year Month]`
- `Customers[city]`
- `Products[category]`
- `Customers[Customer Segment]`

**Filters:**

- Page filter: valid `Date[Date]` range.
- Visual filters: top 10 products and top categories where specified.
- Keep churn as a KPI and filter option, not as a silently excluded population.

### Page 2: Sales Analysis

**Purpose:** Explore revenue, order volume, product mix, and geography.

**KPI cards:**

- `[Total Revenue]`
- `[Total Orders]`
- `[Units Sold]`
- `[Average Order Value]`
- `[Average Selling Price]`

**Charts and tables:**

- Line chart: daily or monthly `Date[Date]`/`Date[Year Month]` by `[Total Revenue]`.
- Combo chart: `Date[Year Month]` with `[Total Revenue]` and `[Total Orders]`.
- Bar chart: `Products[category]` by `[Total Revenue]` and `[Units Sold]`.
- Treemap or ranked bar chart: `Products[product_name]` by `[Total Revenue]`.
- Bar chart: `Customers[city]` by `[Total Revenue]`.
- Detail table: product name, category, `[Total Revenue]`, `[Units Sold]`, `[Total Orders]`.

**Slicers:**

- Date range
- Category
- Product name
- City
- Payment method
- Customer segment

**Filters:**

- Top-N product filter for leaderboard visuals.
- Exclude blank category/product values only after confirming the source quality check is zero.

### Page 3: Customer Analytics

**Purpose:** Understand customer value, behavior, and segment composition.

**KPI cards:**

- `[Total Customers]`
- `[High Value Customers]`
- `[At Risk Customers]`
- `[Average Monthly Spend]`
- `[Average Tenure Months]`

**Charts and tables:**

- Donut chart: `Customers[Customer Segment]` by `[Total Customers]`.
- Column chart: `Customers[city]` by `[Total Customers]` and `[Average Monthly Spend]`.
- Scatter chart: `Customers[tenure_months]` versus `Customers[monthly_spend]`, legend by `Customers[Customer Segment]`, size by `[Total Orders]`.
- Column chart: `Customers[support_calls]` by `[Churned Customers]`.
- Table: customer ID, city, segment, monthly spend, tenure, support calls, `[Total Revenue]`, and churn flag.

**Slicers:**

- Customer segment
- City
- Gender
- Churn flag
- Tenure range

**Filters:**

- Customer detail table can be filtered to `Customers[churn] = 1` or a selected segment.
- Use a Top-N filter only for high-spend customer leaderboards; do not imply the table contains every customer when it is filtered.

### Page 4: Churn Analysis

**Purpose:** Analyze recorded churn and the observable business characteristics associated with it.

**KPI cards:**

- `[Churned Customers]`
- `[Churn Rate]`
- `[Average Support Calls]`
- `[Average Monthly Spend]`
- `[Average Tenure Months]`

**Charts and tables:**

- Donut chart: `Customers[churn]` by `[Total Customers]`.
- Bar chart: `Customers[city]` by `[Churn Rate]`.
- Column chart: `Customers[Customer Segment]` by `[Churned Customers]`.
- Scatter chart: support calls versus monthly spend, legend by churn flag.
- Table: customer ID, city, tenure, monthly spend, support calls, purchase frequency, and churn flag.

**Slicers:**

- City
- Customer segment
- Gender
- Tenure range
- Monthly spend range

**Filters:**

- Use `Customers[churn]` for actual recorded outcomes.
- Add a visual-level filter for `Customers[churn] = 1` only on the churned-customer detail table.
- Do not label recorded churn as predicted risk. Model predictions belong in the Flask churn prediction workflow until a governed prediction table exists.

## 7. Refresh and Validation Checklist

Before publishing or presenting the report:

1. Select **Refresh** in Power BI Desktop and confirm the MySQL credentials are the read-only reporting account.
2. Confirm all four imported tables refresh without errors.
3. Confirm the four relationships are active and have the intended cardinality.
4. Confirm `Date` is marked as the date table and month fields sort chronologically.
5. Confirm `[Orders Without Customer] = 0` and `[Order Items Without Product] = 0`.
6. Compare `[Total Revenue]`, `[Total Orders]`, `[Total Customers]`, `[Average Order Value]`, and `[Churn Rate]` with the existing Python analytics output after both are refreshed from the same database snapshot.
7. Check that slicers cross-filter the visuals and do not create ambiguous relationship paths.
8. Check that no credentials, API keys, or manually typed business results are present in the report.
9. Record the database refresh timestamp and data snapshot used for any interview or presentation.

This repository currently has a known environment limitation: local MySQL authentication has not been successfully validated. Power BI should be treated as ready for connection once MySQL is running, seeded, and accessible through the configured read-only account; this document does not claim that a live Power BI refresh has already succeeded.
