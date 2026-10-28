# Delivery Timeliness and Customer Reviews

Delivered orders that arrived late received lower average review scores than those that arrived on time. The association remains when the comparison is restricted to reviews answered on or after customer receipt, but the gap is smaller. Review timing is therefore important to the interpretation.

## Sample and definitions

The analysis covers delivered orders with actual and estimated delivery dates and a selected review score from 1 to 5. One record per order is selected using the latest answer timestamp, followed by creation timestamp and review ID, as defined in [data quality notes](data_quality_notes.md).

For this case study, a low rating means a score of 1 or 2. Low-rating percentages use reviewed orders in the relevant delivery group and sample as the denominator. Missing ratings are excluded rather than replaced with zero.

Of the 96,470 orders with known delivery timeliness, 95,824 have a selected valid review. There are 153 late orders and 493 on-time orders without reviews. Review coverage is 97.66% for late orders and 99.45% for on-time orders; the comparison does not represent every delivered order's opinion.

## All selected latest reviews

The 6,381 reviewed late orders have an average score of 2.27 out of 5. Among them, 3,983 received a low rating, or 62.42%.

The 89,443 reviewed on-time orders have an average score of 4.29. Among them, 8,289 received a low rating, or 9.27%.

These groups compare the selected review with the order's eventual delivery outcome. They include reviews answered before receipt and should not be described as a comparison of post-delivery satisfaction alone.

## Reviews answered on or after receipt

Restricting the sample using exact answer and receipt timestamps leaves 1,908 late orders and 89,263 on-time orders. The late group has an average score of 3.72, with 371 low ratings, or 19.44%. The on-time group has an average score of 4.29, with 8,258 low ratings, or 9.25%.

The difference remains, but it is smaller than in the full selected-review sample. The restriction removes 4,473 late-order reviews and 180 on-time-order reviews that were answered before receipt. It changes the sample substantially, particularly for late orders, and is not a controlled comparison.

The two samples overlap. An order may appear once in each sample; counts must not be added across samples. Within each sample, every reviewed order has equal weight.

## Business interpretation and limitations

Late delivery is associated with lower ratings in these comparisons. The results do not establish that delays caused the difference, or that improving delivery alone would produce a particular rating increase. Product experience, seller service, order characteristics, and other factors have not been controlled for.

The concentration of pre-receipt reviews among late orders warrants investigation into the experience before a package arrives. Proactive status updates and expectation management are possible areas to assess, but this dataset does not test their effectiveness.

The query is saved in `sql/09_customer_review_comparison.sql`. Selection and validation checks are documented in [data quality notes](data_quality_notes.md); reproduction commands are in [running the analysis](../RUNNING.md).
