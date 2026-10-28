CREATE OR REPLACE VIEW orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    TRY_STRPTIME(order_purchase_timestamp, '%Y-%m-%d %H:%M:%S') AS order_purchase_timestamp,
    TRY_STRPTIME(order_approved_at, '%Y-%m-%d %H:%M:%S') AS order_approved_at,
    TRY_STRPTIME(order_delivered_carrier_date, '%Y-%m-%d %H:%M:%S') AS order_delivered_carrier_date,
    TRY_STRPTIME(order_delivered_customer_date, '%Y-%m-%d %H:%M:%S') AS order_delivered_customer_date,
    TRY_STRPTIME(order_estimated_delivery_date, '%Y-%m-%d %H:%M:%S') AS order_estimated_delivery_date
FROM raw_orders;

CREATE OR REPLACE VIEW customers AS
SELECT * FROM raw_customers;

CREATE OR REPLACE VIEW reviews AS
SELECT
    review_id,
    order_id,
    TRY_CAST(review_score AS INTEGER) AS review_score,
    review_comment_title,
    review_comment_message,
    TRY_STRPTIME(review_creation_date, '%Y-%m-%d %H:%M:%S') AS review_creation_date,
    TRY_STRPTIME(review_answer_timestamp, '%Y-%m-%d %H:%M:%S') AS review_answer_timestamp
FROM raw_reviews;
