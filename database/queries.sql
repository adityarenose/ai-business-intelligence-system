-- Total revenue
SELECT ROUND(COALESCE(SUM(total_amount), 0), 2) AS total_revenue
FROM orders;

-- Monthly revenue
SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
       ROUND(COALESCE(SUM(total_amount), 0), 2) AS monthly_revenue
FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;

-- Category revenue
SELECT p.category,
       ROUND(COALESCE(SUM(oi.line_total), 0), 2) AS category_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- Product revenue
SELECT p.product_id,
       p.product_name,
       p.category,
       ROUND(COALESCE(SUM(oi.line_total), 0), 2) AS product_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY product_revenue DESC;

-- City revenue
SELECT c.city,
       ROUND(COALESCE(SUM(o.total_amount), 0), 2) AS city_revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.city
ORDER BY city_revenue DESC;

-- Customer spending
SELECT c.customer_id,
       c.city,
       c.monthly_spend,
       ROUND(COALESCE(SUM(o.total_amount), 0), 2) AS total_spent,
       COUNT(o.order_id) AS total_orders
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.city, c.monthly_spend
ORDER BY total_spent DESC;

-- Churn rate
SELECT ROUND(COALESCE(AVG(churn), 0) * 100, 2) AS churn_rate_percent
FROM customers;

-- High-value customers
SELECT c.customer_id,
       c.city,
       c.tenure_months,
       ROUND(COALESCE(SUM(o.total_amount), 0), 2) AS lifetime_value,
       c.monthly_spend
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.city, c.tenure_months, c.monthly_spend
HAVING lifetime_value >= 5000
ORDER BY lifetime_value DESC
LIMIT 20;

-- Customers at risk
SELECT c.customer_id,
       c.city,
       c.tenure_months,
       c.monthly_spend,
       c.support_calls,
       c.purchase_frequency,
       c.churn
FROM customers c
WHERE c.churn = 1
ORDER BY c.support_calls DESC, c.monthly_spend ASC
LIMIT 50;
