WITH order_timestamps AS (
    SELECT order_purchase_timestamp AS value FROM raw_orders
    UNION ALL SELECT order_approved_at FROM raw_orders
    UNION ALL SELECT order_delivered_carrier_date FROM raw_orders
    UNION ALL SELECT order_delivered_customer_date FROM raw_orders
    UNION ALL SELECT order_estimated_delivery_date FROM raw_orders
),
review_timestamps AS (
    SELECT review_creation_date AS value FROM raw_reviews
    UNION ALL SELECT review_answer_timestamp FROM raw_reviews
)
SELECT 'order_records' AS check_name, COUNT(*) AS observed_count FROM raw_orders
UNION ALL
SELECT 'customer_records', COUNT(*) FROM raw_customers
UNION ALL
SELECT 'missing_order_ids', COUNT(*) FROM raw_orders WHERE order_id IS NULL
UNION ALL
SELECT 'duplicate_order_ids', COUNT(*) - COUNT(DISTINCT order_id) FROM raw_orders
UNION ALL
SELECT 'missing_order_customer_ids', COUNT(*) FROM raw_orders WHERE customer_id IS NULL
UNION ALL
SELECT 'missing_order_statuses', COUNT(*) FROM raw_orders WHERE order_status IS NULL
UNION ALL
SELECT 'missing_purchase_timestamps', COUNT(*) FROM raw_orders WHERE order_purchase_timestamp IS NULL
UNION ALL
SELECT 'missing_customer_ids', COUNT(*) FROM raw_customers WHERE customer_id IS NULL
UNION ALL
SELECT 'duplicate_customer_ids', COUNT(*) - COUNT(DISTINCT customer_id) FROM raw_customers
UNION ALL
SELECT 'missing_customer_states', COUNT(*) FROM raw_customers WHERE customer_state IS NULL
UNION ALL
SELECT 'orders_without_customers', COUNT(*)
FROM raw_orders LEFT JOIN raw_customers USING (customer_id)
WHERE raw_customers.customer_id IS NULL
UNION ALL
SELECT 'invalid_order_timestamps', COUNT(*) FROM order_timestamps
WHERE value IS NOT NULL AND TRY_STRPTIME(value, '%Y-%m-%d %H:%M:%S') IS NULL
UNION ALL
SELECT 'invalid_review_timestamps', COUNT(*) FROM review_timestamps
WHERE value IS NOT NULL AND TRY_STRPTIME(value, '%Y-%m-%d %H:%M:%S') IS NULL
UNION ALL
SELECT 'missing_review_order_ids', COUNT(*) FROM raw_reviews WHERE order_id IS NULL
UNION ALL
SELECT 'missing_review_ids', COUNT(*) FROM raw_reviews WHERE review_id IS NULL
UNION ALL
SELECT 'invalid_review_scores', COUNT(*) FROM raw_reviews
WHERE review_score IS NULL OR review_score NOT IN ('1', '2', '3', '4', '5')
UNION ALL
SELECT 'reviews_without_orders', COUNT(*)
FROM raw_reviews LEFT JOIN raw_orders USING (order_id)
WHERE raw_orders.order_id IS NULL
UNION ALL
SELECT 'negative_delivered_durations', COUNT(*) FROM orders
WHERE order_status = 'delivered' AND order_delivered_customer_date < order_purchase_timestamp
ORDER BY check_name;
