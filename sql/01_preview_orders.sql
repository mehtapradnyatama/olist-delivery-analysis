-- Inspect delivery fields before calculating performance metrics.
SELECT
    order_id,
    order_status,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM orders
LIMIT 5;
