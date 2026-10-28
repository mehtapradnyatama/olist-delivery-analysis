WITH review_counts AS (
    SELECT
        order_id,
        COUNT(*) AS review_count,
        COUNT(DISTINCT review_score) AS distinct_scores
    FROM reviews
    GROUP BY order_id
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
        ) AS review_rank,
        DENSE_RANK() OVER (
            PARTITION BY order_id
            ORDER BY review_answer_timestamp DESC NULLS LAST,
                review_creation_date DESC NULLS LAST
        ) AS timestamp_rank
    FROM reviews
),
latest_reviews AS (
    SELECT order_id, review_score, review_answer_timestamp
    FROM ranked_reviews
    WHERE review_rank = 1
),
latest_timestamp_ties AS (
    SELECT order_id
    FROM ranked_reviews
    WHERE timestamp_rank = 1
    GROUP BY order_id
    HAVING COUNT(*) > 1
)
SELECT 'review_records' AS check_name, COUNT(*) AS observed_count FROM reviews
UNION ALL
SELECT 'distinct_review_orders', COUNT(DISTINCT order_id) FROM reviews
UNION ALL
SELECT 'distinct_review_ids', COUNT(DISTINCT review_id) FROM reviews
UNION ALL
SELECT 'exact_duplicate_review_records',
    (SELECT COUNT(*) FROM reviews) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM reviews))
UNION ALL
SELECT 'orders_with_multiple_reviews', COUNT(*) FROM review_counts WHERE review_count > 1
UNION ALL
SELECT 'maximum_reviews_per_order', MAX(review_count) FROM review_counts
UNION ALL
SELECT 'orders_with_conflicting_scores', COUNT(*) FROM review_counts WHERE distinct_scores > 1
UNION ALL
SELECT 'invalid_review_scores', COUNT(*) FROM reviews
WHERE TRY_CAST(review_score AS INTEGER) NOT BETWEEN 1 AND 5
    OR TRY_CAST(review_score AS INTEGER) IS NULL
UNION ALL
SELECT 'reviews_missing_timestamps', COUNT(*) FROM reviews
WHERE review_creation_date IS NULL OR review_answer_timestamp IS NULL
UNION ALL
SELECT 'reviews_with_invalid_timestamps', COUNT(*) FROM reviews
WHERE (review_creation_date IS NOT NULL AND TRY_CAST(review_creation_date AS TIMESTAMP) IS NULL)
    OR (review_answer_timestamp IS NOT NULL AND TRY_CAST(review_answer_timestamp AS TIMESTAMP) IS NULL)
UNION ALL
SELECT 'reviews_without_matching_orders', COUNT(*)
FROM reviews LEFT JOIN orders USING (order_id)
WHERE orders.order_id IS NULL
UNION ALL
SELECT 'orders_tied_on_latest_review_timestamps', COUNT(*) FROM latest_timestamp_ties
UNION ALL
SELECT 'delivered_orders_without_reviews', COUNT(*)
FROM orders LEFT JOIN latest_reviews USING (order_id)
WHERE orders.order_status = 'delivered' AND latest_reviews.order_id IS NULL
UNION ALL
SELECT 'raw_review_join_delivered_rows', COUNT(*)
FROM orders LEFT JOIN reviews USING (order_id)
WHERE orders.order_status = 'delivered'
UNION ALL
SELECT 'latest_review_join_delivered_rows', COUNT(*)
FROM orders LEFT JOIN latest_reviews USING (order_id)
WHERE orders.order_status = 'delivered'
UNION ALL
SELECT 'latest_review_join_distinct_delivered_orders', COUNT(DISTINCT orders.order_id)
FROM orders LEFT JOIN latest_reviews USING (order_id)
WHERE orders.order_status = 'delivered'
UNION ALL
SELECT 'latest_reviews_answered_before_customer_delivery', COUNT(*)
FROM orders JOIN latest_reviews USING (order_id)
WHERE orders.order_status = 'delivered'
    AND latest_reviews.review_answer_timestamp < orders.order_delivered_customer_date
ORDER BY check_name;
