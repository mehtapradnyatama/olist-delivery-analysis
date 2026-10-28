# Regional Delivery Performance

Delivery performance is grouped by `customer_state`, representing the customer's destination state or Federal District. The query joins orders to customers using `customer_id` and applies the same calendar-date classification and missing-date exclusions as the overall KPI.

## Rates and affected order counts

AL recorded the highest late-delivery rate: 85 of 397 eligible orders arrived late, or 21.41%. MA followed at 17.43%, with 125 late orders out of 717, and SE at 15.22%, with 51 out of 335.

RJ combines a rate above the overall 6.77% baseline with a large number of affected orders. It recorded 1,495 late orders out of 12,350 eligible orders, or 12.11%. This makes RJ a useful starting point for investigating a substantial concentration of late deliveries.

SP recorded the largest late-order count, at 1,820, despite a below-baseline rate of 4.49%. Its eligible population was 40,494 orders. A ranking based only on percentages would overlook this volume of affected orders.

Investigation priorities should therefore consider both the rate and the number of late orders. AL warrants attention for its high observed rate, while RJ and SP account for larger numbers of late deliveries. These comparisons do not establish where an intervention would produce the greatest benefit.

## Validation and limitations

All 99,441 customer IDs are unique in the customers table. Every order has a matching customer, and no customer state is missing. The delivered-order join retained 96,478 rows and 96,478 distinct order IDs, confirming that it neither dropped nor multiplied delivered orders.

Results cover 27 destination codes. Regional counts reconcile to the overall delivery summary. The query is saved in `sql/07_regional_delivery_performance.sql`.

Small populations make observed rates sensitive to a few orders. For example, RR's 12.20% rate represents 5 late deliveries out of 41 eligible orders. Report denominators alongside percentages when comparing destinations.

Destination is associated with delivery outcomes in these aggregates; it is not a confirmed cause of delay. Differences may also reflect purchase-month mix, seller locations, or other order characteristics. These comparisons cover delivered orders across the full dataset period and do not establish current regional performance.
