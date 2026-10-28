WITH classified_deliveries AS (
    SELECT
        customers.customer_state,
        CASE
            WHEN orders.order_delivered_customer_date IS NULL
                OR orders.order_estimated_delivery_date IS NULL THEN 'Unknown'
            WHEN CAST(orders.order_delivered_customer_date AS DATE)
                > CAST(orders.order_estimated_delivery_date AS DATE) THEN 'Late'
            ELSE 'On time'
        END AS delivery_timeliness
    FROM orders
    -- customer_id is unique in customers; the join preserves one row per order.
    LEFT JOIN customers
        ON orders.customer_id = customers.customer_id
    WHERE orders.order_status = 'delivered'
),
regional_counts AS (
    SELECT
        customer_state,
        COUNT(*) AS delivered_orders,
        SUM(CASE WHEN delivery_timeliness = 'Unknown' THEN 1 ELSE 0 END)
            AS unknown_timeliness_orders,
        SUM(CASE WHEN delivery_timeliness <> 'Unknown' THEN 1 ELSE 0 END)
            AS eligible_delivered_orders,
        SUM(CASE WHEN delivery_timeliness = 'Late' THEN 1 ELSE 0 END)
            AS late_orders,
        SUM(CASE WHEN delivery_timeliness = 'On time' THEN 1 ELSE 0 END)
            AS on_time_orders
    FROM classified_deliveries
    GROUP BY customer_state
)
SELECT
    customer_state,
    delivered_orders,
    unknown_timeliness_orders,
    eligible_delivered_orders,
    late_orders,
    on_time_orders,
    ROUND(100.0 * late_orders / NULLIF(eligible_delivered_orders, 0), 2)
        AS late_delivery_rate_pct
FROM regional_counts
ORDER BY late_delivery_rate_pct DESC NULLS LAST,
    eligible_delivered_orders DESC,
    customer_state;
