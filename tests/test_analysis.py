"""Business-rule tests use small synthetic fixtures, never portfolio findings."""

import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.analysis import (
    PROJECT_ROOT, REQUIRED_COLUMNS, SOURCE_FILES, run_analysis, validate_results,
)


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="olist's test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.dataset = self.root / 'dataset'
        self.dataset.mkdir()
        self.customers = [
            {'customer_id': 'c1', 'customer_unique_id': 'u1', 'customer_state': 'SP'},
            {'customer_id': 'c2', 'customer_unique_id': 'u2', 'customer_state': 'RJ'},
        ]

        def order(identifier, customer, actual, estimated, purchase='2018-01-01 00:00:00', status='delivered'):
            return {'order_id': identifier, 'customer_id': customer, 'order_status': status,
                    'order_purchase_timestamp': purchase,
                    'order_delivered_customer_date': actual,
                    'order_estimated_delivery_date': estimated}

        self.orders = [
            order('o1', 'c1', '2018-01-03 10:00:00', '2018-01-04 00:00:00'),
            order('o2', 'c2', '2018-01-05 15:00:00', '2018-01-05 00:00:00'),
            order('o3', 'c2', '2018-02-08 10:00:00', '2018-02-06 00:00:00', '2018-02-01 00:00:00'),
            order('o4', 'c1', None, '2018-01-05 00:00:00'),
            order('o5', 'c2', '2018-01-03 10:00:00', None),
            order('o6', 'c1', '2018-01-10 00:00:00', '2018-01-05 00:00:00', status='canceled'),
            order('o7', 'c1', None, None),
        ]

        def review(identifier, order_id, score, answered):
            return {'review_id': identifier, 'order_id': order_id, 'review_score': score,
                    'review_creation_date': answered, 'review_answer_timestamp': answered}

        self.reviews = [
            review('r1', 'o1', 5, '2018-01-04 10:00:00'),
            review('r2', 'o2', 4, '2018-01-04 10:00:00'),
            review('r3-old', 'o3', 1, '2018-02-07 10:00:00'),
            review('r3-new', 'o3', 2, '2018-02-09 10:00:00'),
            review('r4', 'o4', 1, '2018-01-06 10:00:00'),
        ]

    def write_sources(self, delimiter=','):
        for table, rows in [('orders', self.orders), ('customers', self.customers), ('reviews', self.reviews)]:
            with (self.dataset / SOURCE_FILES[table]).open('w', encoding='utf-8', newline='') as target:
                writer = csv.DictWriter(target, fieldnames=REQUIRED_COLUMNS[table], delimiter=delimiter)
                writer.writeheader()
                writer.writerows(rows)

    def analyze(self):
        self.write_sources()
        return run_analysis(self.dataset)[0]

    def restrict_orders(self, identifiers):
        self.orders = [row for row in self.orders if row['order_id'] in identifiers]
        self.reviews = [row for row in self.reviews if row['order_id'] in identifiers]

    def cli(self, output):
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'scripts/run_pipeline.py'),
             '--data-dir', str(self.dataset), '--output-dir', str(output)],
            cwd=self.root, text=True, capture_output=True,
        )

    def test_same_estimated_day_is_on_time_and_canceled_orders_are_excluded(self):
        summary = self.analyze()['delivery_summary'][0]
        self.assertEqual(summary['total_delivered_orders'], 6)
        self.assertEqual(summary['unknown_timeliness_orders'], 3)
        self.assertEqual(summary['eligible_delivered_orders'], 3)
        self.assertEqual(summary['late_orders'], 1)
        self.assertEqual(summary['on_time_orders'], 2)
        self.assertEqual(summary['late_delivery_rate_pct'], 33.33)

    def test_duration_does_not_require_an_estimated_date(self):
        results = self.analyze()
        self.assertEqual(results['delivery_duration'][0]['measurable_delivered_orders'], 4)
        self.assertEqual(results['delivery_summary'][0]['eligible_delivered_orders'], 3)

    def test_latest_review_is_selected_without_multiplying_orders(self):
        results = self.analyze()
        quality = {row['check_name']: row['observed_count'] for row in results['review_data_quality']}
        self.assertEqual(quality['raw_review_join_delivered_rows'], 7)
        self.assertEqual(quality['latest_review_join_delivered_rows'], 6)
        late = next(row for row in results['customer_review_comparison']
                    if row['review_sample'] == 'All latest reviews' and row['delivery_timeliness'] == 'Late')
        self.assertEqual(late['reviewed_orders'], 1)
        self.assertEqual(late['average_review_score'], 2)
        self.assertEqual(late['low_rating_rate_pct'], 100)

    def test_pre_receipt_review_is_excluded_only_from_restricted_sample(self):
        rows = self.analyze()['customer_review_comparison']
        counts = {(row['review_sample'], row['delivery_timeliness']): row['reviewed_orders'] for row in rows}
        self.assertEqual(counts[('All latest reviews', 'On time')], 2)
        self.assertEqual(counts[('Answered on/after delivery', 'On time')], 1)

    def test_monthly_and_regional_groups_reconcile(self):
        results = self.analyze()
        self.assertEqual(len(results['monthly_delivery_performance']), 2)
        self.assertEqual(len(results['regional_delivery_performance']), 2)
        for name in ['monthly_delivery_performance', 'regional_delivery_performance']:
            self.assertEqual(sum(row['delivered_orders'] for row in results[name]), 6)
            self.assertEqual(sum(row['late_orders'] for row in results[name]), 1)

    def test_no_reviews_produces_no_rating_average(self):
        self.reviews = []
        results = self.analyze()
        self.assertEqual(results['customer_review_comparison'], [])
        quality = {row['check_name']: row['observed_count'] for row in results['review_data_quality']}
        self.assertEqual(quality['delivered_orders_without_reviews'], 6)

    def test_zero_eligible_orders_has_null_rates(self):
        self.restrict_orders({'o4', 'o5', 'o7'})
        summary = self.analyze()['delivery_summary'][0]
        self.assertEqual(summary['eligible_delivered_orders'], 0)
        self.assertIsNone(summary['late_delivery_rate_pct'])
        self.assertIsNone(summary['on_time_delivery_rate_pct'])

    def test_no_delivered_orders_has_zero_counts_and_null_measures(self):
        self.restrict_orders({'o6'})
        results = self.analyze()
        summary = results['delivery_summary'][0]
        self.assertEqual(summary['total_delivered_orders'], 0)
        self.assertEqual(summary['late_orders'], 0)
        self.assertIsNone(summary['late_delivery_rate_pct'])
        self.assertIsNone(results['delivery_duration'][0]['average_delivery_days'])
        self.assertEqual(results['monthly_delivery_performance'], [])

    def test_invalid_source_values_are_rejected(self):
        cases = ['timestamp', 'duplicate_order', 'duplicate_customer', 'unmatched_customer',
                 'orphan_review', 'rating', 'negative_duration']
        for case in cases:
            with self.subTest(case=case):
                orders, customers, reviews = copy.deepcopy((self.orders, self.customers, self.reviews))
                if case == 'timestamp':
                    self.orders[0]['order_delivered_customer_date'] = '03/01/18 10.00'
                elif case == 'duplicate_order':
                    self.orders.append(dict(self.orders[0]))
                elif case == 'duplicate_customer':
                    self.customers.append(dict(self.customers[0]))
                elif case == 'unmatched_customer':
                    self.orders[0]['customer_id'] = 'missing'
                elif case == 'orphan_review':
                    self.reviews[0]['order_id'] = 'missing'
                elif case == 'rating':
                    self.reviews[0]['review_score'] = 6
                elif case == 'negative_duration':
                    self.orders[0]['order_delivered_customer_date'] = '2017-12-31 00:00:00'
                with self.assertRaisesRegex(ValueError, 'Source validation failed'):
                    self.analyze()
                self.orders, self.customers, self.reviews = orders, customers, reviews

    def test_ambiguous_latest_review_is_rejected(self):
        duplicate = dict(self.reviews[3])
        duplicate.update(review_id='r3-tie', review_score=3)
        self.reviews.append(duplicate)
        with self.assertRaisesRegex(ValueError, 'orders_tied_on_latest_review_timestamps'):
            self.analyze()

    def test_modified_csv_separator_is_rejected(self):
        self.write_sources(delimiter=';')
        with self.assertRaisesRegex(ValueError, 'original comma-separated CSV'):
            run_analysis(self.dataset)

    def test_validation_catches_inconsistent_summary(self):
        results = self.analyze()
        results['delivery_summary'][0]['late_orders'] += 1
        with self.assertRaisesRegex(ValueError, 'delivery categories reconcile'):
            validate_results(results)

    def test_exports_are_reproducible_portable_and_preserve_sources(self):
        self.write_sources()
        source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in self.dataset.iterdir()}
        output = self.root / 'output'
        first = self.cli(output)
        self.assertEqual(first.returncode, 0, first.stderr)
        files = {path.name: path.read_bytes() for path in output.iterdir()}
        self.assertEqual(len(files), 16)
        second = self.cli(output)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(files, {path.name: path.read_bytes() for path in output.iterdir()})
        self.assertEqual(source_hashes, {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                        for path in self.dataset.iterdir()})
        self.assertTrue(json.loads(files['validation_report.json'])['passed'])
        self.assertEqual(json.loads(files['monthly_delivery_performance.json'])[0]['purchase_month'], '2018-01-01')
        manifest = json.loads(files['analysis_manifest.json'])
        self.assertEqual(set(manifest['sources']), set(SOURCE_FILES.values()))

    def test_failed_validation_preserves_existing_output(self):
        self.reviews[0]['review_score'] = 6
        self.write_sources()
        output = self.root / 'output'
        output.mkdir()
        sentinel = output / 'delivery_summary.csv'
        sentinel.write_text('existing output', encoding='utf-8')
        result = self.cli(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Source validation failed', result.stderr)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'existing output')
        self.assertEqual(len(list(output.iterdir())), 1)

    def test_empty_groups_export_headers_and_json_null(self):
        self.restrict_orders({'o6'})
        self.write_sources()
        output = self.root / 'empty-output'
        result = self.cli(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((output / 'monthly_delivery_performance.json').read_text()), [])
        self.assertIn('purchase_month', (output / 'monthly_delivery_performance.csv').read_text())
        summary = json.loads((output / 'delivery_summary.json').read_text())[0]
        self.assertIsNone(summary['late_delivery_rate_pct'])


@unittest.skipUnless(all((PROJECT_ROOT / 'dataset' / name).is_file() for name in SOURCE_FILES.values()),
                     'Download the Olist source files to run the real-data regression test.')
class OlistRegressionTests(unittest.TestCase):
    def test_actual_source_metrics_match_verified_baseline(self):
        results, checks = run_analysis(PROJECT_ROOT / 'dataset')
        self.assertTrue(all(check['passed'] for check in checks))
        self.assertEqual(results['delivery_summary'][0], {
            'total_delivered_orders': 96478, 'unknown_timeliness_orders': 8,
            'eligible_delivered_orders': 96470, 'late_orders': 6534,
            'on_time_orders': 89936, 'late_delivery_rate_pct': 6.77,
            'on_time_delivery_rate_pct': 93.23,
        })
        self.assertEqual(len(results['monthly_delivery_performance']), 23)
        self.assertEqual(len(results['regional_delivery_performance']), 27)
        self.assertEqual(results['delivery_duration'][0]['average_delivery_days'], 12.56)
        self.assertEqual(results['delivery_duration'][0]['median_delivery_days'], 10.22)
        reviews = {(row['review_sample'], row['delivery_timeliness']): row
                   for row in results['customer_review_comparison']}
        self.assertEqual(reviews[('All latest reviews', 'Late')]['reviewed_orders'], 6381)
        self.assertEqual(reviews[('All latest reviews', 'Late')]['low_rating_rate_pct'], 62.42)
        self.assertEqual(reviews[('Answered on/after delivery', 'Late')]['reviewed_orders'], 1908)
        self.assertEqual(reviews[('Answered on/after delivery', 'Late')]['low_rating_rate_pct'], 19.44)


if __name__ == '__main__':
    unittest.main()
