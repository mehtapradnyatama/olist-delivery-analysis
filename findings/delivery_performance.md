# Delivery Performance

## Overall late-delivery rate

Of the 96,470 delivered orders with usable actual and estimated delivery dates, 6,534 arrived after their estimated delivery date. The overall late-delivery rate is **6.77%**. The remaining 89,936 orders arrived on or before the estimated date.

The rate is calculated as 6,534 / 96,470 × 100. It describes delivered orders whose timeliness can be assessed, rather than all orders in the dataset. Eight delivered orders without an actual delivery date are excluded from this calculation and retained in the total delivered-order count.

Delivery dates are compared at calendar-day level. Arrival on the estimated day counts as on time, even when the actual delivery timestamp is later than midnight.

The calculation is defined in `sql/02_delivery_performance.sql`. Validation rules and checks are documented in [data quality notes](data_quality_notes.md) and [running the analysis](../RUNNING.md).

The overall rate establishes a baseline. It does not explain why orders were late or establish an effect on customer reviews. Further results are documented in [monthly delivery performance](monthly_delivery_performance.md), [delivery duration](delivery_duration.md), [regional delivery performance](regional_delivery_performance.md), and [customer review comparisons](customer_review_comparison.md).
