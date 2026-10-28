"""Validate saved workbook values, formulas, tables, and chart bindings."""

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
SHEETS = ['KPI Summary', 'Monthly Delivery', 'Regional Performance',
          'Customer Satisfaction', 'Data Dictionary']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cells(archive, path, strings):
    tree = ET.fromstring(archive.read(path))
    output = {}
    for cell in tree.findall('.//s:sheetData/s:row/s:c', NS):
        kind = cell.get('t', 'n')
        value = cell.findtext('s:v', default=None, namespaces=NS)
        require(kind != 'e', 'Saved formula error in {}!{}'.format(path, cell.get('r')))
        if kind == 's' and value is not None:
            value = strings[int(value)]
        elif kind == 'inlineStr':
            value = ''.join(element.text or '' for element in cell.findall('.//s:t', NS))
        elif kind == 'n' and value is not None:
            value = float(value)
        output[cell.get('r')] = {'value': value, 'formula': cell.findtext('s:f', default=None, namespaces=NS)}
    return output


def close(actual, expected, label, tolerance=1e-9):
    require(isinstance(actual, (int, float)) and abs(actual - expected) <= tolerance,
            '{}: expected {}, found {}'.format(label, expected, actual))


def validate(workbook_path, data_dir):
    data = {name: json.loads((data_dir / (name + '.json')).read_text(encoding='utf-8'))
            for name in ['delivery_summary', 'monthly_delivery_performance',
                         'regional_delivery_performance', 'customer_review_comparison', 'delivery_duration']}
    with zipfile.ZipFile(workbook_path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        require([sheet.get('name') for sheet in workbook.findall('s:sheets/s:sheet', NS)] == SHEETS,
                'Unexpected worksheet names or order.')
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(element.itertext()) for element in
                       ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        sheets = {name: cells(archive, 'xl/worksheets/sheet{}.xml'.format(index + 1), strings)
                  for index, name in enumerate(SHEETS)}
        summary = sheets['KPI Summary']
        source = data['delivery_summary'][0]
        for address, key in [('C7', 'total_delivered_orders'), ('C8', 'unknown_timeliness_orders'),
                             ('C9', 'eligible_delivered_orders'), ('C10', 'late_orders'), ('C11', 'on_time_orders')]:
            close(summary[address]['value'], source[key], address)
            require(summary[address]['formula'] is not None, address + ' must remain a formula.')
        close(summary['C12']['value'], source['late_orders'] / source['eligible_delivered_orders'], 'Late rate')
        for row in range(7, 13):
            close(summary['J' + str(row)]['value'], 0, 'SQL reconciliation')
        for address, key in [('C14', 'average_delivery_days'), ('C15', 'median_delivery_days')]:
            close(summary[address]['value'], data['delivery_duration'][0][key], key)

        for sheet_name, source_name, key in [('Monthly Delivery', 'monthly_delivery_performance', 'purchase_month'),
                                             ('Regional Performance', 'regional_delivery_performance', 'customer_state')]:
            sheet = sheets[sheet_name]
            for index, record in enumerate(data[source_name]):
                row = index + 7
                label = sheet['B' + str(row)]['value']
                if key == 'purchase_month':
                    if isinstance(label, (int, float)):
                        label = (datetime(1899, 12, 30) + timedelta(days=label)).date().isoformat()
                    else:
                        label = datetime.fromisoformat(label.replace('Z', '+00:00')).date().isoformat()
                require(label == record[key], 'Source group label mismatch.')
                for column, field in [('C', 'delivered_orders'), ('D', 'unknown_timeliness_orders'),
                                      ('E', 'eligible_delivered_orders'), ('F', 'late_orders'), ('G', 'on_time_orders')]:
                    close(sheet[column + str(row)]['value'], record[field], sheet_name + '/' + field)
                close(sheet['H' + str(row)]['value'] * 100, record['late_delivery_rate_pct'],
                      sheet_name + '/rate', tolerance=0.00501)
                require(sheet['H' + str(row)]['formula'] is not None, 'Rate formula was lost.')

        reviews = {(row['review_sample'], row['delivery_timeliness']): row for row in data['customer_review_comparison']}
        for row, sample, status in [(7, 'All latest reviews', 'On time'), (8, 'All latest reviews', 'Late'),
                                    (14, 'Answered on/after delivery', 'On time'), (15, 'Answered on/after delivery', 'Late')]:
            sheet, record = sheets['Customer Satisfaction'], reviews[(sample, status)]
            for column, field in [('C', 'reviewed_orders'), ('D', 'average_review_score'), ('E', 'low_rating_orders')]:
                close(sheet[column + str(row)]['value'], record[field], sample + '/' + field)
            close(sheet['F' + str(row)]['value'] * 100, record['low_rating_rate_pct'], sample + '/low-rating rate', 0.00501)
            require(sheet['F' + str(row)]['formula'] is not None, 'Low-rating formula was lost.')

        chart_paths = sorted(path for path in archive.namelist()
                             if '/charts/' in path and path.endswith('.xml') and '_rels' not in path)
        require(len(chart_paths) == 3, 'Expected three native charts.')
        expected_points = [[20, 20], [10], [2, 2]]
        for index, path in enumerate(chart_paths):
            tree = ET.fromstring(archive.read(path))
            bindings = [item.text for item in tree.findall('.//c:f', NS)]
            require(bindings and all('!' in binding and '#REF!' not in binding for binding in bindings),
                    'Chart has a missing or broken cell binding.')
            points = [int(item.get('val')) for item in tree.findall('.//c:ser/c:val/c:numRef/c:numCache/c:ptCount', NS)]
            require(points == expected_points[index], 'Unexpected chart point count: ' + path)
            colors = {item.get('val') for item in tree.findall('.//a:srgbClr', NS)}
            require('087F8C' in colors, 'Chart series color was lost.')
            if index == 2:
                require('BC542C' in colors, 'Late-rating series color was lost.')
        tables = [path for path in archive.namelist() if path.startswith('xl/tables/') and path.endswith('.xml')]
        require(len(tables) == 5, 'Expected five filterable Excel tables.')
        for path in tables:
            require(ET.fromstring(archive.read(path)).find('s:autoFilter', NS) is not None,
                    'Missing table filter: ' + path)
    print('Workbook validation passed: 5 sheets, source-matched values, saved formula results, 5 filterable tables, and 3 bound native charts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, default=ROOT / 'excel/delivery_analysis.xlsx')
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data/processed')
    args = parser.parse_args()
    validate(args.workbook, args.data_dir)


if __name__ == '__main__':
    main()
