WITH eligible_deliveries AS (
    SELECT
        order_id,
        order_delivered_customer_date,
        CASE
            WHEN CAST(order_delivered_customer_date AS DATE)
                > CAST(order_estimated_delivery_date AS DATE) THEN 'Late'
            ELSE 'On time'
        END AS delivery_timeliness
    FROM orders
    WHERE order_status = 'delivered'
        AND order_delivered_customer_date IS NOT NULL
        AND order_estimated_delivery_date IS NOT NULL
),
ranked_reviews AS (
    SELECT
        order_id,
        review_score,
        review_answer_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_answer_timestamp DESC NULLS LAST,
                review_creation_date DESC NULLS LAST,
                review_id DESC
        ) AS review_rank
    FROM reviews
),
reviewed_orders AS (
    SELECT
        orders.order_id,
        orders.delivery_timeliness,
        orders.order_delivered_customer_date,
        reviews.review_score,
        reviews.review_answer_timestamp
    FROM eligible_deliveries AS orders
    JOIN ranked_reviews AS reviews ON orders.order_id = reviews.order_id
    WHERE reviews.review_rank = 1
        AND reviews.review_score BETWEEN 1 AND 5
),
review_samples AS (
    SELECT 'All latest reviews' AS review_sample, delivery_timeliness, review_score
    FROM reviewed_orders
    UNION ALL
    -- Restrict the second sample to reviews answered at or after customer receipt.
    SELECT 'Answered on/after delivery' AS review_sample, delivery_timeliness, review_score
    FROM reviewed_orders
    WHERE review_answer_timestamp >= order_delivered_customer_date
)
SELECT
    review_sample,
    delivery_timeliness,
    COUNT(*) AS reviewed_orders,
    ROUND(AVG(review_score), 2) AS average_review_score,
    SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) AS low_rating_orders,
    ROUND(100.0 * SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS low_rating_rate_pct
FROM review_samples
GROUP BY review_sample, delivery_timeliness
ORDER BY review_sample, delivery_timeliness;
