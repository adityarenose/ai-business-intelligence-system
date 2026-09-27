USE ai_bi_system;

LOAD DATA INFILE 'C:/Users/Aditya/OneDrive/Documents/AI-Business-Intelligence-System/data/raw/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, age, gender, city, tenure_months, monthly_spend, support_calls, purchase_frequency, churn);

LOAD DATA INFILE 'C:/Users/Aditya/OneDrive/Documents/AI-Business-Intelligence-System/data/raw/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_id, product_name, category, unit_price);

LOAD DATA INFILE 'C:/Users/Aditya/OneDrive/Documents/AI-Business-Intelligence-System/data/raw/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, customer_id, order_date, total_amount, payment_method);

LOAD DATA INFILE 'C:/Users/Aditya/OneDrive/Documents/AI-Business-Intelligence-System/data/raw/order_items.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_item_id, order_id, product_id, quantity, unit_price, line_total);

