WITH delivered_durations AS (
    SELECT
        -- Use elapsed time, including partial days, from purchase to customer receipt.
        DATE_DIFF('second', order_purchase_timestamp, order_delivered_customer_date)
            / 86400.0 AS delivery_duration_days
    FROM orders
    WHERE order_status = 'delivered'
        AND order_purchase_timestamp IS NOT NULL
        AND order_delivered_customer_date IS NOT NULL
        AND order_delivered_customer_date >= order_purchase_timestamp
)
SELECT
    COUNT(*) AS measurable_delivered_orders,
    ROUND(AVG(delivery_duration_days), 2) AS average_delivery_days,
    ROUND(MEDIAN(delivery_duration_days), 2) AS median_delivery_days
FROM delivered_durations;
