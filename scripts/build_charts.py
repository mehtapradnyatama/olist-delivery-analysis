"""Create publication charts from validated aggregate JSON files."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import textwrap

from analysis import PROJECT_ROOT, QUERIES, validate_results, validate_source

os.environ.setdefault('MPLCONFIGDIR', str(PROJECT_ROOT / '.cache/matplotlib'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter


NAVY = '#18364D'
TEAL = '#087F8C'
ORANGE = '#BC542C'
SLATE = '#607386'
LIGHT = '#B5C6D3'
GRID = '#E5EBF0'


def style():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 11,
        'text.color': NAVY, 'axes.labelcolor': SLATE,
        'xtick.color': SLATE, 'ytick.color': SLATE,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.edgecolor': '#D3DEE6', 'axes.titleweight': 'bold',
        'axes.axisbelow': True, 'grid.color': GRID,
        'svg.fonttype': 'none', 'svg.hashsalt': 'olist-delivery',
    })


def header(figure, title, subtitle):
    figure.suptitle(title, x=0.08, y=0.97, ha='left', fontsize=20, fontweight='bold')
    figure.text(0.08, 0.905, subtitle, fontsize=11, color=SLATE)


def footer(figure, text):
    figure.text(0.08, 0.025, textwrap.fill(text, width=150), fontsize=9, color=SLATE,
                va='bottom', linespacing=1.5)


def save(figure, output_dir, name, title):
    figure.savefig(output_dir / (name + '.png'), dpi=180, facecolor='white',
                   metadata={'Software': 'Olist delivery analysis'})
    figure.savefig(output_dir / (name + '.svg'), facecolor='white',
                   metadata={'Date': None, 'Creator': 'Olist delivery analysis', 'Title': title})
    plt.close(figure)


def monthly_chart(results, output_dir):
    rows = [row for row in results['monthly_delivery_performance']
            if '2017-01-01' <= row['purchase_month'] <= '2018-08-01'
            and row['late_delivery_rate_pct'] is not None]
    if not rows:
        raise ValueError('No eligible purchase cohorts in the monthly reporting window.')
    dates = [datetime.fromisoformat(row['purchase_month']) for row in rows]
    rates = [row['late_delivery_rate_pct'] for row in rows]
    counts = [row['eligible_delivered_orders'] for row in rows]
    baseline = results['delivery_summary'][0]['late_delivery_rate_pct']
    peak_index = max(range(len(rows)), key=lambda index: rates[index])
    peak = rows[peak_index]
    figure, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True,
                                gridspec_kw={'height_ratios': [3, 1]})
    figure.subplots_adjust(left=0.10, right=0.96, top=0.81, bottom=0.17, hspace=0.13)
    header(figure, 'Late deliveries varied substantially over time',
           'Purchase-month cohorts | January 2017 to August 2018 | calendar-date classification')
    axis, volume = axes
    axis.plot(dates, rates, color=TEAL, linewidth=2.6, marker='o', markersize=4)
    axis.fill_between(dates, rates, color=TEAL, alpha=0.06)
    axis.axhline(baseline, color=SLATE, linestyle=(0, (5, 4)), linewidth=1.2,
                label='Overall late-delivery rate: {:.2f}%'.format(baseline))
    axis.set_ylim(0, max(rates) + 6)
    axis.set_ylabel('Late-delivery rate')
    axis.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    axis.grid(axis='y')
    axis.legend(loc='upper left', frameon=False, fontsize=10)
    axis.scatter([dates[peak_index]], [rates[peak_index]], color=ORANGE, s=65, zorder=4)
    annotation = '{}: {:.2f}%\n{:,} late / {:,} eligible orders'.format(
        dates[peak_index].strftime('%b %Y'), peak['late_delivery_rate_pct'],
        peak['late_orders'], peak['eligible_delivered_orders'])
    axis.annotate(annotation, xy=(dates[peak_index], rates[peak_index]),
                  xytext=(-130, 20), textcoords='offset points', fontsize=10,
                  color=ORANGE, arrowprops={'arrowstyle': '-', 'color': ORANGE})
    volume.bar(dates, counts, width=20, color=LIGHT)
    volume.set_ylabel('Eligible\norders', fontsize=10)
    volume.yaxis.set_major_formatter(FuncFormatter(lambda value, _: '{:,.0f}'.format(value)))
    volume.grid(axis='y')
    ticks = dates[::2]
    if ticks[-1] != dates[-1]:
        ticks.append(dates[-1])
    volume.set_xticks(ticks)
    volume.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    footer(figure, 'Source: Olist orders. Sparse 2016 cohorts remain in the data exports. '
           'The dashed baseline uses all eligible delivered orders; the trend window is shown above.')
    save(figure, output_dir, 'monthly_delivery_performance', 'Monthly late-delivery rate and eligible order volume')


def state_color(state):
    return {'AL': ORANGE, 'RJ': NAVY, 'SP': TEAL}.get(state, LIGHT)


def regional_chart(results, output_dir):
    rows = [row for row in results['regional_delivery_performance']
            if row['late_delivery_rate_pct'] is not None]
    if not rows:
        raise ValueError('No eligible destination groups for the regional chart.')
    by_rate = sorted(rows, key=lambda row: (-row['late_delivery_rate_pct'], row['customer_state']))[:10]
    by_count = sorted(rows, key=lambda row: (-row['late_orders'], row['customer_state']))[:10]
    baseline = results['delivery_summary'][0]['late_delivery_rate_pct']
    figure, axes = plt.subplots(1, 2, figsize=(13, 8))
    figure.subplots_adjust(left=0.14, right=0.96, top=0.79, bottom=0.18, wspace=0.55)
    header(figure, 'Regional priorities depend on rate and volume',
           'Customer destination | one row per delivered order | full dataset period')
    axis, volume = axes
    labels = ['{}  (n={:,})'.format(row['customer_state'], row['eligible_delivered_orders']) for row in by_rate]
    bars = axis.barh(labels, [row['late_delivery_rate_pct'] for row in by_rate],
                     color=[state_color(row['customer_state']) for row in by_rate], height=0.65)
    axis.invert_yaxis()
    axis.set_title('Highest late-delivery rates', loc='left', pad=16, fontsize=12)
    axis.set_xlabel('Late-delivery rate')
    axis.set_xlim(0, max(row['late_delivery_rate_pct'] for row in by_rate) * 1.32)
    axis.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    axis.axvline(baseline, color=SLATE, linestyle=(0, (5, 4)), linewidth=1)
    axis.grid(axis='x')
    axis.bar_label(bars, labels=['{:.2f}%'.format(row['late_delivery_rate_pct']) for row in by_rate],
                   padding=5, fontsize=10, color=NAVY)
    labels = ['{}  ({:.2f}%)'.format(row['customer_state'], row['late_delivery_rate_pct']) for row in by_count]
    bars = volume.barh(labels, [row['late_orders'] for row in by_count],
                       color=[state_color(row['customer_state']) for row in by_count], height=0.65)
    volume.invert_yaxis()
    volume.set_title('Largest late-order counts', loc='left', pad=16, fontsize=12)
    volume.set_xlabel('Late orders')
    volume.set_xlim(0, max(row['late_orders'] for row in by_count) * 1.25)
    volume.xaxis.set_major_formatter(FuncFormatter(lambda value, _: '{:,.0f}'.format(value)))
    volume.grid(axis='x')
    volume.bar_label(bars, labels=['{:,}'.format(row['late_orders']) for row in by_count],
                     padding=5, fontsize=10, color=NAVY)
    footer(figure, 'Source: Olist orders and customers. Up to 10 destinations are shown in each ranking; all 27 remain in the exports. '
           'n = eligible delivered orders. Dashed line = overall {:.2f}%. Small samples make rates sensitive to a few orders.'.format(baseline))
    save(figure, output_dir, 'regional_delivery_performance', 'Regional late-delivery rates and late-order counts')


def review_chart(results, output_dir):
    lookup = {(row['review_sample'], row['delivery_timeliness']): row
              for row in results['customer_review_comparison']}
    samples = ['All latest reviews', 'Answered on/after delivery']
    if any((sample, status) not in lookup for sample in samples for status in ['On time', 'Late']):
        raise ValueError('Both delivery groups and review samples are required for the rating chart.')
    figure, axes = plt.subplots(1, 2, figsize=(13, 7.5))
    figure.subplots_adjust(left=0.08, right=0.96, top=0.78, bottom=0.19, wspace=0.30)
    header(figure, 'Review timing changes the size of the rating gap',
           'One latest review per order | groups describe eventual delivery timeliness')
    positions = [0, 1.3]
    width = 0.32
    for axis, metric, title in [
        (axes[0], 'average_review_score', 'Average review score'),
        (axes[1], 'low_rating_rate_pct', 'Low ratings: scores 1 or 2'),
    ]:
        for status, offset, color in [('On time', -width / 2, TEAL), ('Late', width / 2, ORANGE)]:
            rows = [lookup[(sample, status)] for sample in samples]
            values = [row[metric] for row in rows]
            bars = axis.bar([position + offset for position in positions], values,
                            width=width, color=color, label=status)
            labels = [('{:.2f}' if metric == 'average_review_score' else '{:.2f}%').format(row[metric])
                      + '\nn={:,}'.format(row['reviewed_orders']) for row in rows]
            axis.bar_label(bars, labels=labels, padding=5, fontsize=9, color=NAVY)
        axis.set_title(title, loc='left', fontsize=12, pad=14)
        axis.set_xticks(positions, ['All latest\nreviews', 'On/after\nreceipt'])
        axis.grid(axis='y')
        axis.set_xlim(-0.65, 1.95)
    axes[0].set_ylim(0, 5)
    axes[0].set_ylabel('Mean score (1-5)')
    axes[1].set_ylim(0, 100)
    axes[1].yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='upper right', bbox_to_anchor=(0.96, 0.875), ncol=2,
                   frameon=False, fontsize=10)
    footer(figure, 'Source: Olist orders and reviews. Samples overlap; do not add their counts. '
           'The restricted sample uses exact receipt and answer timestamps. These comparisons do not establish causation.')
    save(figure, output_dir, 'customer_review_comparison', 'Ratings and low-rating shares by review sample and delivery timeliness')


def build_charts(data_dir, output_dir):
    data_dir, output_dir = Path(data_dir), Path(output_dir)
    results = {name: json.loads((data_dir / (name + '.json')).read_text(encoding='utf-8'))
               for name in QUERIES}
    validate_source(results['source_data_quality'])
    validate_results(results)
    output_dir.mkdir(parents=True, exist_ok=True)
    style()
    monthly_chart(results, output_dir)
    regional_chart(results, output_dir)
    review_chart(results, output_dir)
    return output_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=PROJECT_ROOT / 'data/processed')
    parser.add_argument('--output-dir', type=Path, default=PROJECT_ROOT / 'assets/charts')
    args = parser.parse_args()
    output = build_charts(args.data_dir, args.output_dir)
    print('Created 3 charts in PNG and SVG: {}'.format(output.resolve()))


if __name__ == '__main__':
    main()
