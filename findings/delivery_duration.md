# Delivery Duration

Delivered orders took an average of **12.56 days** from purchase to customer receipt. The median was **10.22 days**. These measures cover 96,470 orders with recorded purchase and receipt timestamps and a nonnegative elapsed time.

Of the 96,478 orders marked as delivered, 8 lacked a receipt timestamp and were excluded. No delivered order with both timestamps recorded had a receipt timestamp earlier than purchase.

## Metric definition

The query in `sql/06_delivery_duration.sql` calculates elapsed seconds between purchase and receipt, then divides by 86,400 to express the result in days. Partial days and weekends are included. The calculation uses the timestamps as recorded, without timezone conversion.

An estimated delivery date is not required for this metric. Duration measures how long an order took to arrive; timeliness compares the arrival date with the estimated date. An order with a long delivery duration can still be on time if its estimate allowed for that duration.

## Business interpretation

The mean and median provide different views of the purchase-to-receipt experience. The median indicates that roughly half of measurable delivered orders arrived within about 10.22 days. The higher mean should be considered alongside the distribution before setting operational targets.

This duration includes the time before carrier handoff as well as transport to the customer. It is not a measure of courier transit time alone. The aggregate does not establish which operational stage accounts for delays or whether 12.56 days meets a service target.
