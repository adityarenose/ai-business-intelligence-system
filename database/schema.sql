CREATE DATABASE IF NOT EXISTS ai_bi_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_bi_system;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    city VARCHAR(100) NOT NULL,
    tenure_months INT NOT NULL,
    monthly_spend DECIMAL(10,2) NOT NULL,
    support_calls INT NOT NULL,
    purchase_frequency DECIMAL(8,2) NOT NULL,
    churn TINYINT(1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    CHECK (age BETWEEN 18 AND 100),
    CHECK (tenure_months >= 0),
    CHECK (monthly_spend >= 0),
    CHECK (support_calls >= 0),
    CHECK (purchase_frequency >= 0),
    CHECK (churn IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    product_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(80) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (product_id),
    CHECK (unit_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
    order_id INT NOT NULL,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (total_amount >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT NOT NULL,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (order_item_id),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CHECK (quantity > 0),
    CHECK (unit_price >= 0),
    CHECK (line_total >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_customers_churn ON customers(churn);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_amount ON orders(total_amount);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
