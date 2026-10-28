# Running the Analysis

The analysis uses DuckDB through Python. SQL contains the preparation and metric definitions; Python loads the sources, runs validation, and writes aggregate outputs. Matplotlib creates the static figures. The current setup has been verified with Python 3.9.6, DuckDB 1.4.5, and [Matplotlib 3.9.4](https://pypi.org/project/matplotlib/3.9.4/), which supports Python 3.9.

## Setup

Open a terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place these original CSV files in `dataset/`:

- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_reviews_dataset.csv`

Keep the comma-separated headers and original timestamp format, `YYYY-MM-DD HH:MM:SS`. Save Excel work separately as `.xlsx`. Source CSV files are excluded from Git tracking.

## Run the pipeline

```bash
python scripts/run_pipeline.py
```

The program loads a snapshot of the three CSV files into an in-memory DuckDB database. It retains raw strings for source checks and prepares typed `orders`, `customers`, and `reviews` views using `sql/00_prepare_data.sql`.

Source validation checks required identifiers, unique order and customer keys, timestamp formats, rating values, relationships between tables, and negative delivery durations. Missing actual or estimated delivery dates remain allowed: they make delivery timeliness unknown and are excluded from delivery-rate denominators. Source errors stop the pipeline before aggregate files are replaced.

The analysis then checks monthly and regional totals against the overall population, verifies rate calculations, and checks review selection and sample sizes. A tie on the latest review answer and creation timestamps stops validation for investigation rather than silently accepting an ambiguous selection.

Seven result sets are exported to `data/processed/`, each as CSV and JSON:

- `source_data_quality`: source record counts and validation issues.
- `delivery_summary`: delivered, eligible, late, on-time, and unknown counts and rates.
- `monthly_delivery_performance`: results by purchase month.
- `delivery_duration`: measurable order count, mean duration, and median duration.
- `regional_delivery_performance`: results by customer destination code.
- `review_data_quality`: review coverage, multiplicity, timing, and join checks.
- `customer_review_comparison`: mean ratings and low-rating proportions for both review samples.

`validation_report.json` records the aggregate checks that passed. `analysis_manifest.json` records source and SQL file hashes, the DuckDB version, and exported row counts. Identical inputs and code produce identical output files; no run timestamp is embedded.

Outputs contain aggregates only. They do not include order IDs, customer IDs, coordinates, or review text. JSON uses ISO dates and `null` for undefined measures. An empty result still produces a CSV header and an empty JSON list. Percentage fields ending in `_pct` already contain percentage values: `6.77` means 6.77%.

To use a different input or output folder:

```bash
python scripts/run_pipeline.py --data-dir /path/to/dataset --output-dir /path/to/results
```

The output folder must be separate from the source dataset folder. The pipeline does not modify the source CSV files or the Excel workbook.

## Generate figures

Run the pipeline and create figures together:

```bash
python scripts/run_pipeline.py --charts
```

To rebuild figures from existing validated JSON outputs:

```bash
python scripts/build_charts.py
```

Three figures are saved to `assets/charts/` as PNG and SVG: monthly delivery performance, regional rates and counts, and the customer-review comparison. The monthly figure uses the January 2017-August 2018 reporting window; sparse 2016 cohorts remain in the aggregate exports. The regional figure shows up to ten destinations in each ranking, with all 27 retained in the exports. Review figures display both overlapping samples with their respective denominators.

The chart builder rechecks the exported counts and rates before rendering. `--chart-dir` on the pipeline controls the figure folder; `--output-dir` on the standalone chart builder does the same. Matplotlib's local font cache is stored in `.cache/`, which is excluded from Git tracking.

## Inspect one query

```bash
python scripts/run_sql.py sql/02_delivery_performance.sql
```

This loads and validates the source tables, runs the selected SQL file, and prints its result. It does not export files. The same command works with other analysis files and personal exercises. The preparation script is run automatically; analysis SQL expects its source views to exist.

The SQL files for preview, eligibility, and late-order counts are incremental exploration queries. The pipeline runs the combined delivery summary and the monthly, duration, regional, review-quality, and rating analyses.

## Excel workbook

The portfolio workbook is in `excel/delivery_analysis.xlsx`. It contains aggregate inputs, Excel formulas, filterable tables, and native charts. Its inputs are a saved snapshot; running the pipeline does not overwrite the workbook. Refresh instructions are in [the Excel guide](excel/EXCEL_GUIDE.md).

After recalculating and saving the workbook, validate its saved contents against the pipeline outputs:

```bash
python scripts/validate_workbook.py
```

The validator uses Python's standard library and does not require the spreadsheet authoring runtime. It checks saved values and native feature bindings, not live Microsoft Excel behavior.

## Run tests

```bash
python -m unittest discover -s tests -v
```

The suite tests calendar-date classification, missing dates, canceled orders, review selection, review timing, monthly and regional reconciliation, zero denominators, input rejection, reproducible exports, and source preservation. Small synthetic fixtures are used only for tests; portfolio findings come from the Olist CSV files.

A separate regression test checks the verified Olist results when all three source files are present. It is skipped when the dataset has not been downloaded. Fixture tests can still run without the real data.
