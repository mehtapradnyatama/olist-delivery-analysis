"""Load source tables, execute analysis SQL, and validate aggregate results."""

import csv
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = {
    'orders': 'olist_orders_dataset.csv',
    'customers': 'olist_customers_dataset.csv',
    'reviews': 'olist_order_reviews_dataset.csv',
}
REQUIRED_COLUMNS = {
    'orders': ['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp',
               'order_approved_at', 'order_delivered_carrier_date',
               'order_delivered_customer_date', 'order_estimated_delivery_date'],
    'customers': ['customer_id', 'customer_unique_id', 'customer_zip_code_prefix',
                  'customer_city', 'customer_state'],
    'reviews': ['review_id', 'order_id', 'review_score', 'review_comment_title',
                'review_comment_message', 'review_creation_date', 'review_answer_timestamp'],
}
QUERIES = {
    'source_data_quality': '00_source_data_quality.sql',
    'delivery_summary': '02_delivery_performance.sql',
    'monthly_delivery_performance': '05_monthly_delivery_performance.sql',
    'delivery_duration': '06_delivery_duration.sql',
    'regional_delivery_performance': '07_regional_delivery_performance.sql',
    'review_data_quality': '08_review_data_quality.sql',
    'customer_review_comparison': '09_customer_review_comparison.sql',
}


def load_database(dataset_dir):
    """Load strings first so quality checks can detect invalid source values."""
    dataset_dir = Path(dataset_dir).resolve()
    for table, filename in SOURCE_FILES.items():
        path = dataset_dir / filename
        if not path.is_file():
            raise ValueError('Missing source file: {}'.format(path))
        with path.open(encoding='utf-8-sig', newline='') as source:
            columns = next(csv.reader(source), [])
        missing = set(REQUIRED_COLUMNS[table]) - set(columns)
        if missing:
            raise ValueError('{}: missing columns {}. Use the original comma-separated CSV.'.format(
                filename, ', '.join(sorted(missing))))

    connection = duckdb.connect()
    try:
        for table, filename in SOURCE_FILES.items():
            connection.read_csv(str(dataset_dir / filename), header=True,
                                all_varchar=True, delimiter=',').create('raw_' + table)
        connection.execute((PROJECT_ROOT / 'sql/00_prepare_data.sql').read_text(encoding='utf-8'))
    except Exception:
        connection.close()
        raise
    return connection


def read_query(sql_path, dataset_dir):
    query = Path(sql_path).read_text(encoding='utf-8')
    # Keep older personal exercises with direct CSV references runnable from any folder.
    for filename in SOURCE_FILES.values():
        absolute = str(Path(dataset_dir).resolve() / filename).replace("'", "''")
        query = query.replace("'dataset/{}'".format(filename), "'{}'".format(absolute))
    return query


def query_records(connection, sql_path, dataset_dir):
    result = connection.execute(read_query(sql_path, dataset_dir))
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def validate_source(rows):
    counts = {row['check_name']: row['observed_count'] for row in rows}
    errors = {name: count for name, count in counts.items()
              if name not in ('order_records', 'customer_records') and count != 0}
    if counts['order_records'] == 0:
        errors['order_records'] = 'source contains no orders'
    if errors:
        raise ValueError('Source validation failed: {}'.format(errors))


def validate_results(results):
    """Check cohort totals and rating denominators before exporting results."""
    checks = []

    def require(name, condition):
        if not condition:
            raise ValueError('Analysis validation failed: ' + name)
        checks.append({'check': name, 'passed': True})

    summary = results['delivery_summary'][0]
    eligible = summary['eligible_delivered_orders']
    require('delivery categories reconcile',
            summary['late_orders'] + summary['on_time_orders'] == eligible)
    require('delivered population reconciles',
            eligible + summary['unknown_timeliness_orders'] == summary['total_delivered_orders'])
    for status, count_key in [('late', 'late_orders'), ('on_time', 'on_time_orders')]:
        expected = round(100 * summary[count_key] / eligible, 2) if eligible else None
        require(status + ' overall rate is correct', summary[status + '_delivery_rate_pct'] == expected)

    totals = {'delivered_orders': 'total_delivered_orders',
              'unknown_timeliness_orders': 'unknown_timeliness_orders',
              'eligible_delivered_orders': 'eligible_delivered_orders',
              'late_orders': 'late_orders', 'on_time_orders': 'on_time_orders'}
    for output, group_key in [('monthly_delivery_performance', 'purchase_month'),
                              ('regional_delivery_performance', 'customer_state')]:
        rows = results[output]
        require(output + ' has unique nonmissing groups',
                len({row[group_key] for row in rows}) == len(rows)
                and all(row[group_key] is not None for row in rows))
        for key, summary_key in totals.items():
            require(output + ': ' + key + ' reconciles',
                    sum(row[key] for row in rows) == summary[summary_key])
        for row in rows:
            denominator = row['eligible_delivered_orders']
            require(output + ': categories reconcile for ' + str(row[group_key]),
                    row['late_orders'] + row['on_time_orders'] == denominator
                    and denominator + row['unknown_timeliness_orders'] == row['delivered_orders'])
            expected = round(100 * row['late_orders'] / denominator, 2) if denominator else None
            require(output + ': rate is correct for ' + str(row[group_key]),
                    row['late_delivery_rate_pct'] == expected)

    quality = {row['check_name']: row['observed_count'] for row in results['review_data_quality']}
    for key in ['invalid_review_scores', 'reviews_missing_timestamps',
                'reviews_with_invalid_timestamps', 'reviews_without_matching_orders',
                'orders_tied_on_latest_review_timestamps']:
        require(key + ' is zero', quality[key] == 0)
    for key in ['latest_review_join_delivered_rows', 'latest_review_join_distinct_delivered_orders']:
        require(key + ' preserves delivered orders', quality[key] == summary['total_delivered_orders'])
    require('one selected review per reviewed order',
            quality['distinct_review_orders'] <= quality['review_records'])

    groups = {(row['review_sample'], row['delivery_timeliness']): row
              for row in results['customer_review_comparison']}
    require('review sample/group pairs are unique', len(groups) == len(results['customer_review_comparison']))
    for (sample, status), row in groups.items():
        require('valid rating summary for ' + sample + '/' + status,
                row['reviewed_orders'] > 0 and 1 <= row['average_review_score'] <= 5
                and 0 <= row['low_rating_orders'] <= row['reviewed_orders'])
        expected = round(100 * row['low_rating_orders'] / row['reviewed_orders'], 2)
        require('low-rating denominator for ' + sample + '/' + status,
                row['low_rating_rate_pct'] == expected)
        baseline = groups.get(('All latest reviews', status))
        require('review subset size for ' + sample + '/' + status,
                baseline is not None and row['reviewed_orders'] <= baseline['reviewed_orders'])
    for status, key in [('Late', 'late_orders'), ('On time', 'on_time_orders')]:
        baseline = groups.get(('All latest reviews', status))
        require('review coverage does not exceed ' + status + ' orders',
                (baseline['reviewed_orders'] if baseline else 0) <= summary[key])

    duration = results['delivery_duration'][0]
    require('duration sample does not exceed delivered population',
            0 <= duration['measurable_delivered_orders'] <= summary['total_delivered_orders'])
    for key in ['average_delivery_days', 'median_delivery_days']:
        require(key + ' is valid',
                (duration[key] is None if duration['measurable_delivered_orders'] == 0
                 else duration[key] is not None and duration[key] >= 0))
    return checks


def run_analysis(dataset_dir):
    with load_database(dataset_dir) as connection:
        source = query_records(connection, PROJECT_ROOT / 'sql' / QUERIES['source_data_quality'], dataset_dir)
        validate_source(source)
        results = {'source_data_quality': source}
        for name, filename in QUERIES.items():
            if name != 'source_data_quality':
                results[name] = query_records(connection, PROJECT_ROOT / 'sql' / filename, dataset_dir)
        checks = validate_results(results)
    return results, checks
