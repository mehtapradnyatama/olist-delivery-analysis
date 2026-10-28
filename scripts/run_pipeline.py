"""Run validated SQL analyses and export aggregate CSV and JSON files."""

import argparse
import csv
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import duckdb

from analysis import PROJECT_ROOT, QUERIES, SOURCE_FILES, run_analysis


CSV_COLUMNS = {
    'source_data_quality': ['check_name', 'observed_count'],
    'delivery_summary': ['total_delivered_orders', 'unknown_timeliness_orders',
                         'eligible_delivered_orders', 'late_orders', 'on_time_orders',
                         'late_delivery_rate_pct', 'on_time_delivery_rate_pct'],
    'monthly_delivery_performance': ['purchase_month', 'delivered_orders',
                                     'unknown_timeliness_orders', 'eligible_delivered_orders',
                                     'late_orders', 'on_time_orders', 'late_delivery_rate_pct'],
    'delivery_duration': ['measurable_delivered_orders', 'average_delivery_days', 'median_delivery_days'],
    'regional_delivery_performance': ['customer_state', 'delivered_orders',
                                      'unknown_timeliness_orders', 'eligible_delivered_orders',
                                      'late_orders', 'on_time_orders', 'late_delivery_rate_pct'],
    'review_data_quality': ['check_name', 'observed_count'],
    'customer_review_comparison': ['review_sample', 'delivery_timeliness', 'reviewed_orders',
                                    'average_review_score', 'low_rating_orders', 'low_rating_rate_pct'],
}


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError('Unsupported JSON value: {}'.format(type(value).__name__))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=json_value,
                               allow_nan=False) + '\n', encoding='utf-8')


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_results(results, checks, dataset_dir, output_dir):
    output_dir = output_dir.resolve()
    dataset_dir = dataset_dir.resolve()
    if output_dir == dataset_dir or dataset_dir in output_dir.parents:
        raise ValueError('Choose an output folder separate from the source dataset.')
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    sql_files = ['00_prepare_data.sql'] + list(QUERIES.values())
    manifest = {
        'schema_version': 1,
        'duckdb_version': duckdb.__version__,
        'sources': {filename: {'sha256': file_hash(dataset_dir / filename)}
                    for filename in SOURCE_FILES.values()},
        'sql_files': {filename: {'sha256': file_hash(PROJECT_ROOT / 'sql' / filename)}
                      for filename in sql_files},
        'outputs': {name: {'rows': len(rows), 'formats': ['csv', 'json']}
                    for name, rows in results.items()},
    }
    report = {
        'passed': True,
        'source_checks_passed': True,
        'aggregate_checks_passed': len(checks),
        'checks': checks,
    }
    # Complete validation before replacing any published aggregate files.
    with tempfile.TemporaryDirectory(prefix='.analysis-', dir=str(output_dir.parent)) as temporary:
        staging = Path(temporary)
        for name, rows in results.items():
            with (staging / (name + '.csv')).open('w', encoding='utf-8', newline='') as target:
                writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS[name])
                writer.writeheader()
                writer.writerows(rows)
            write_json(staging / (name + '.json'), rows)
        write_json(staging / 'validation_report.json', report)
        write_json(staging / 'analysis_manifest.json', manifest)
        output_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(staging.iterdir()):
            path.replace(output_dir / path.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=PROJECT_ROOT / 'dataset')
    parser.add_argument('--output-dir', type=Path, default=PROJECT_ROOT / 'data/processed')
    parser.add_argument('--charts', action='store_true', help='Also generate PNG and SVG charts')
    parser.add_argument('--chart-dir', type=Path, default=PROJECT_ROOT / 'assets/charts')
    args = parser.parse_args()
    try:
        results, checks = run_analysis(args.data_dir)
        export_results(results, checks, args.data_dir, args.output_dir)
        if args.charts:
            from build_charts import build_charts
            build_charts(args.output_dir, args.chart_dir)
    except (ValueError, OSError, duckdb.Error) as error:
        print('Pipeline failed: {}'.format(error), file=sys.stderr)
        return 1
    for name, rows in results.items():
        print('{}: {} rows exported as CSV and JSON'.format(name, len(rows)))
    print('Validation passed: {} aggregate checks.'.format(len(checks)))
    print('Output folder: {}'.format(args.output_dir.resolve()))
    if args.charts:
        print('Created 3 charts in PNG and SVG: {}'.format(args.chart_dir.resolve()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
