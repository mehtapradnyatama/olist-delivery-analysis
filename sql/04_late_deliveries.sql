SELECT
    COUNT(*) AS late_orders
FROM orders
WHERE order_status = 'delivered'
    AND order_delivered_customer_date IS NOT NULL
    AND order_estimated_delivery_date IS NOT NULL
    -- Compare calendar dates so arrival on the estimated day counts as on time.
    AND CAST(order_delivered_customer_date AS DATE)
        > CAST(order_estimated_delivery_date AS DATE);
