# Data Quality Notes

Initial checks on order completeness and the rules used to assess delivery performance.

## DQ-001: Missing delivery dates on completed orders

Source: `dataset/olist_orders_dataset.csv`.

The orders dataset contains 99,441 records, of which 96,478 have a status of `delivered`. Eight of these delivered orders have no recorded customer delivery date, leaving 96,470 with both actual and estimated delivery timestamps populated.

Without an actual delivery date, the eight affected orders cannot be classified as on time or late. The reason for the missing dates is unknown.

Filtering delivered orders for blank customer delivery dates in Excel returned 8 records. A separate check of the source CSV using Python confirmed these counts.

### Treatment

Retain these records in the source data and the total delivered-order count. Assign their delivery timeliness as **unknown** and exclude them from both the numerator and denominator of on-time and late-delivery rates.

### Delivery classification

A delivered order is on time when its actual delivery date falls on or before the estimated delivery date. It is late when the actual date falls after the estimate. If either date is missing or invalid, its timeliness is unknown.

The comparison uses calendar dates because the analysis measures arrival against the estimated delivery day. An order received on that day is on time, regardless of the recorded hour. Early deliveries are included in the same category.

**Late-delivery rate (%) = late delivered orders / delivered orders with valid actual and estimated delivery dates × 100.**

### Validation scope

The initial completeness check identified 96,470 records with both delivery date fields populated. A subsequent Python check confirmed that all nonempty order timestamps could be parsed using `YYYY-MM-DD HH:MM:SS` and that all 99,441 order IDs were unique. Purchase-to-receipt chronology is covered in [delivery duration](delivery_duration.md); customer and review relationships are documented below. Repeatable source checks and automated tests are described in [running the analysis](../RUNNING.md).

## DQ-002: Source CSV formatting changed during exploration

The initial orders file used comma separators and timestamps in `YYYY-MM-DD HH:MM:SS` format. During exploration, the source path was found to contain a semicolon-separated version with timestamps in `DD/MM/YY HH.MM` format. That version did not preserve seconds.

Parsing the reformatted version reproduced the initial counts: 96,470 delivered orders with usable dates, including 6,534 late orders and 89,936 on-time orders. The change did not affect calendar-date classification, but removed precision needed for elapsed-time calculations.

The recovery check found that `dataset/olist_orders_dataset.csv` again uses comma separators and timestamps with seconds. All nonempty order timestamps parsed successfully, and the late, on-time, and unknown counts matched the initial results. The reformatted working copy was kept separately during recovery; Excel work is now saved as `delivery_analysis.xlsx`.

Keep the source CSV separate from analysis work. Save the Excel workbook in `.xlsx` format to retain formulas, filters, and formatting.

## DQ-003: Orders-to-customers relationship

The customers table contains 99,441 records and 99,441 distinct `customer_id` values. Every order has a matching customer ID, and all customer records have a destination state recorded.

A left join on `orders.customer_id = customers.customer_id`, restricted to delivered orders, returned 96,478 rows and 96,478 distinct order IDs. There were no unmatched delivered orders. The join therefore preserves one row per delivered order in this dataset.

Regional aggregation produced 27 destination groups. Delivered, unknown, eligible, late, and on-time counts sum to the corresponding overall KPI counts. Each regional count and late-delivery rate was also checked against an independent Python calculation from the source CSV files.

This check covers the orders-to-customers relationship. The review relationship is assessed separately below because an order can have multiple review records.

## DQ-004: Review multiplicity and timing

The reviews file contains 99,224 records for 98,673 distinct orders. There are 547 orders with multiple review records, with a maximum of three records per order. Of these orders, 202 have different scores across their review records.

The file contains 98,410 distinct `review_id` values and no exact duplicate records across all fields. A repeated review ID therefore cannot be treated as sufficient evidence that a full record should be dropped. All review scores are integers from 1 to 5. No review creation or answer timestamps are missing or invalid, and every review record has a matching order.

### Order-level review selection

For the customer-review comparison, retain one record per order: the record with the latest `review_answer_timestamp`, followed by the latest `review_creation_date`. Use descending `review_id` as a deterministic fallback. No orders are tied on the latest answer and creation timestamp pair in the current dataset.

This is an analytical selection rule. Multiple records do not, by themselves, establish that a customer revised an earlier review, and the selected record should not be described as a confirmed final opinion.

A direct left join from delivered orders to all review records produces 97,007 rows for 96,478 delivered orders. Selecting one review per order before joining preserves 96,478 rows and 96,478 distinct order IDs. Of these orders, 646 have no review. Retain them in delivery KPIs, but exclude them from rating averages and rating-based denominators; do not replace missing ratings with zero.

### Review timing

Among delivered orders with a recorded receipt timestamp, 4,653 selected latest reviews were answered before customer receipt. The full selected-review sample therefore cannot be described as post-delivery satisfaction.

The comparison in [customer reviews](customer_review_comparison.md) reports the association between eventual delivery timeliness and the selected order-level score. A second sample is restricted to reviews answered on or after receipt. Neither comparison establishes a causal effect of delays on ratings.

The 17 checks in `sql/08_review_data_quality.sql` matched an independent Python calculation from the source CSV files. This verifies the review profile, timestamp and score checks, coverage, join counts, and selected-review timing. Rating comparisons are available in `sql/09_customer_review_comparison.sql` and have also been checked against an independent Python calculation. The pipeline exports these checks on each run; persistent tests cover review selection, join preservation, timing, and the verified source results.
