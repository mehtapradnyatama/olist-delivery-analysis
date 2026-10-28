# Monthly Delivery Performance

Delivered orders are grouped by purchase month. This keeps each order in the month it was placed, even when delivery occurred later. The late-delivery rate for each month uses delivered orders from that purchase cohort with both actual and estimated delivery dates available.

The query in `sql/05_monthly_delivery_performance.sql` returns 23 purchase-month cohorts. The aggregated output is stored in `data/processed/monthly_delivery_performance.csv`.

## Variation over time

For purchase cohorts from January 2017 through August 2018, March 2018 had the highest late-delivery rate: 1,328 of 7,003 eligible orders arrived late, or 18.96%. February 2018 recorded 14.13%, while November 2017 recorded 12.40%.

The rate fell to 4.50% for orders purchased in April 2018 and reached 1.16% in June, before rising to 6.19% in August. Performance varied over time; the sequence does not show continuous improvement.

March 2018 is a priority for further investigation because both the rate and the number of affected orders were high. The current analysis does not identify the cause. Regional and review comparisons can help narrow the investigation.

## Interpretation limits

The 2016 cohorts are retained in the output but are sparse: September contains one eligible delivered order, October contains 265, and December contains one. September's 100% late-delivery rate therefore represents a single order. It should not be treated as evidence of the worst sustained operational performance. No delivered purchase cohort is present for November 2016; an absent cohort does not imply a 0% late-delivery rate.

The trend discussion focuses on the 20 consecutive purchase months from January 2017 through August 2018, each with at least 750 eligible delivered orders. This reporting window does not establish that the dataset captures all business activity during those months.

These are outcomes for delivered orders, not all orders placed in each month. The monthly labels refer to purchase dates, not the dates on which delays occurred. Calendar-date comparisons and missing-date exclusions follow the definitions in [data quality notes](data_quality_notes.md).

For a combined period, calculate the rate from total late orders divided by total eligible orders. A simple average of monthly percentages would give small and large cohorts equal weight.
