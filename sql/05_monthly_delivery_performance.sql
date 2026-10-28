WITH classified_deliveries AS (
    SELECT
        -- Group by purchase month to keep late arrivals in their original order cohort.
        CAST(DATE_TRUNC('month', order_purchase_timestamp) AS DATE) AS purchase_month,
        CASE
            WHEN order_delivered_customer_date IS NULL
                OR order_estimated_delivery_date IS NULL THEN 'Unknown'
            WHEN CAST(order_delivered_customer_date AS DATE)
                > CAST(order_estimated_delivery_date AS DATE) THEN 'Late'
            ELSE 'On time'
        END AS delivery_timeliness
    FROM orders
    WHERE order_status = 'delivered'
),
monthly_counts AS (
    SELECT
        purchase_month,
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
    GROUP BY purchase_month
)
SELECT
    purchase_month,
    delivered_orders,
    unknown_timeliness_orders,
    eligible_delivered_orders,
    late_orders,
    on_time_orders,
    ROUND(100.0 * late_orders / NULLIF(eligible_delivered_orders, 0), 2)
        AS late_delivery_rate_pct
FROM monthly_counts
ORDER BY purchase_month;
