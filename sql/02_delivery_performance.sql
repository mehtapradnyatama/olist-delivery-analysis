WITH classified_deliveries AS (
    SELECT
        CASE
            WHEN order_delivered_customer_date IS NULL
                OR order_estimated_delivery_date IS NULL THEN 'Unknown'
            -- Arrival on the estimated calendar day is on time.
            WHEN CAST(order_delivered_customer_date AS DATE)
                > CAST(order_estimated_delivery_date AS DATE) THEN 'Late'
            ELSE 'On time'
        END AS delivery_timeliness
    FROM orders
    WHERE order_status = 'delivered'
),
delivery_counts AS (
    SELECT
        COUNT(*) AS total_delivered_orders,
        COALESCE(SUM(CASE WHEN delivery_timeliness = 'Unknown' THEN 1 ELSE 0 END), 0)
            AS unknown_timeliness_orders,
        COALESCE(SUM(CASE WHEN delivery_timeliness <> 'Unknown' THEN 1 ELSE 0 END), 0)
            AS eligible_delivered_orders,
        COALESCE(SUM(CASE WHEN delivery_timeliness = 'Late' THEN 1 ELSE 0 END), 0)
            AS late_orders,
        COALESCE(SUM(CASE WHEN delivery_timeliness = 'On time' THEN 1 ELSE 0 END), 0)
            AS on_time_orders
    FROM classified_deliveries
)
SELECT
    total_delivered_orders,
    unknown_timeliness_orders,
    eligible_delivered_orders,
    late_orders,
    on_time_orders,
    ROUND(100.0 * late_orders / NULLIF(eligible_delivered_orders, 0), 2)
        AS late_delivery_rate_pct,
    ROUND(100.0 * on_time_orders / NULLIF(eligible_delivered_orders, 0), 2)
        AS on_time_delivery_rate_pct
FROM delivery_counts;
