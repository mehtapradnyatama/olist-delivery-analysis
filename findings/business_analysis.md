# Delivery Performance: Business Assessment and Recommendations

## Business Problem

For January 2017–August 2018 purchase cohorts, 6.79% of 96,203 delivered orders with actual and estimated delivery dates available arrived late. March 2018 recorded the highest monthly rate: 18.96%, affecting 1,328 of 7,003 eligible orders.

No company service target was available. Historical results provide an internal reference, but do not establish whether performance met customer commitments or operational targets. The March peak identifies a period for investigation.

Late deliveries may increase customer dissatisfaction and support workload. Their effect on repeat purchases, sales, and operating costs would require additional evidence.

## Investigation Priorities

### 1. Locate the stage that slowed in March

Compare purchase-to-carrier-handover and carrier-handover-to-receipt durations for March 2018 against March 2017, February 2018, and April 2018. Examine median and upper-percentile durations alongside order volumes and destination mix. Seller comparisons would require adding order-item and seller data to the current analysis.

The working hypotheses are a preparation or collection bottleneck, and disruption during transit. Available timestamps can identify where elapsed time increased. Capacity records, collection schedules, and dated incident reports would be needed to explain why. A longer stage duration alone does not establish a cause or a stage-specific service breach.

### 2. Prioritize destinations using rates and counts

Across the full dataset period, RJ recorded 1,495 late orders and a 12.11% late-delivery rate. SP had a lower rate of 4.49% but the largest late-order count, at 1,820. Together they accounted for 50.73% of late orders. AL had the highest observed rate, 21.41%, representing 85 of 397 eligible orders.

Review RJ for its combination of scale and elevated lateness, retain SP when assessing the number of affected customers, and examine AL's high rate with its smaller denominator in view. Compare similar purchase periods before choosing an intervention population.

### 3. Examine the experience while customers wait

Late orders averaged 2.27 out of 5 in the selected-review sample, compared with 4.29 for on-time orders. Restricting reviews to those answered on or after receipt changes these averages to 3.72 and 4.29. The samples overlap and differ substantially in composition.

The smaller gap after restricting review timing supports examining the experience before receipt. Review customer-update practices and complaint handling with operations and customer service. Communication logs are not included in the dataset.

## Conditional Actions

If delays increased before carrier handover, review seller preparation workflows, stock availability, processing queues, and collection arrangements. Determine whether the constraint relates to demand, capacity, inventory, or coordination before selecting a remedy.

If delays increased after handover, examine affected destinations and request shipment-level explanations from logistics partners. Carrier and route comparisons require additional logistics records.

Assess an overdue-order queue with clear ownership and customer-update responsibilities. Test any proposed change on a limited population before wider adoption, with an operational owner and evaluation period agreed in advance.

## Measures of Success

Track monthly late-delivery rate together with late-order counts and eligible order volume. A smaller late-order count alone may reflect lower demand.

Monitor purchase-to-receipt duration using the median and upper percentiles. For a preparation or collection intervention, also track purchase-to-carrier-handover duration.

Agree numerical targets after reviewing the baseline, service commitments, and capacity. Evaluate comparable cohorts, accounting for volume, seasonality, and order mix; use a controlled rollout where feasible. Extending estimated delivery dates alone would not demonstrate faster delivery.

## Scope and Limitations

This assessment uses historical Olist marketplace data. Recommendations have not been validated through stakeholder interviews or internal operational records. The proposed stage-duration comparisons and interventions have not been performed or evaluated; no operational or financial improvement is claimed.

The Tableau dashboard covers January 2017–August 2018. Regional and review findings use the full dataset period. Sparse 2016 cohorts remain in the analysis outputs but are excluded from the dashboard trend.

Orders are grouped by purchase month. Arrival after the estimated calendar date counts as late; arrival on that date counts as on time. Delivery-rate denominators include only delivered orders with both dates available, excluding canceled and unresolved orders.

Missing reviews, review timing, small regional samples, and unmeasured order characteristics limit interpretation. The observed relationship between lateness and ratings does not establish causation.

Supporting results: [monthly performance](monthly_delivery_performance.md), [regional performance](regional_delivery_performance.md), [delivery duration](delivery_duration.md), and [customer reviews](customer_review_comparison.md). Definitions and validation are in [data quality notes](data_quality_notes.md).
