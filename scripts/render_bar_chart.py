#!/usr/bin/env python3
"""Render one numeric series to SVG. Standard library only; never invent data."""
import argparse
import html
import json
import math
from pathlib import Path


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')
    if any(ord(c) < 32 and c not in '\n\t\r' for c in value):
        raise ValueError(f'{field} contains invalid XML control characters')
    return value.strip()


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    for key in ('title', 'unit', 'source'):
        text(data.get(key), key)
    items = data.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 30:
        raise ValueError('items must contain 1 to 30 entries')
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Each item must be an object')
        label = text(item.get('label'), 'label')
        if label in seen:
            raise ValueError('Duplicate category labels: split or combine deliberately')
        seen.add(label)
        value = item.get('value')
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Each value must be numeric; missing values are not zero')
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError('Values must be finite')
    return data


def render(data):
    validate(data)
    items = data['items']
    width, left, right, top, row = 960, 260, 110, 110, 44
    bottom = top + row * len(items)
    height = bottom + 92
    values = [i['value'] for i in items]
    lo, hi = min(0, min(values)), max(0, max(values))
    if lo == hi:
        hi = 1
    # Normalize first to avoid overflow when finite values have opposite huge signs.
    magnitude = max(abs(lo), abs(hi))
    low, high = lo / magnitude, hi / magnitude
    plot_width = width - left - right
    x = lambda v: left + (v / magnitude - low) / (high - low) * plot_width
    zero = x(0)
    esc = lambda s: html.escape(str(s), quote=True)
    short = lambda s, n: s if len(s) <= n else s[:n - 1] + '…'
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">',
           f'<title id="chart-title">{esc(data["title"])}</title>',
           f'<desc id="chart-desc">单位：{esc(data["unit"])}。来源：{esc(data["source"])}。' + esc('；'.join(f'{i["label"]}: {i["value"]}' for i in items)) + '</desc>',
           '<style>text{font-family:"PingFang SC","Microsoft YaHei",Arial,sans-serif;fill:#172033} .small{font-size:13px;fill:#64748b}</style>',
           f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           f'<text x="28" y="40" font-size="22" font-weight="600">{esc(short(data["title"], 48))}</text>',
           f'<text x="28" y="68" class="small">单位：{esc(short(data["unit"], 50))}</text>']
    for j in range(5):
        fraction = j / 4
        value = (low * (1 - fraction) + high * fraction) * magnitude
        xx = left + fraction * plot_width
        svg.extend([f'<line x1="{xx:.2f}" x2="{xx:.2f}" y1="{top - 12}" y2="{bottom}" stroke="#e2e8f0"/>',
                    f'<text x="{xx:.2f}" y="{bottom + 24}" text-anchor="middle" class="small">{value:.4g}</text>'])
    svg.append(f'<line x1="{zero:.2f}" x2="{zero:.2f}" y1="{top - 12}" y2="{bottom}" stroke="#64748b"/>')
    for index, item in enumerate(items):
        yy = top + index * row
        end = x(item['value'])
        bar_left, bar_width = min(zero, end), abs(end - zero)
        color = '#2563eb' if item['value'] >= 0 else '#ea580c'
        label = text(item['label'], 'label')
        svg.extend([f'<text x="{left - 16}" y="{yy + 22}" font-size="15" text-anchor="end"><title>{esc(label)}</title>{esc(short(label, 15))}</text>',
                    f'<rect x="{bar_left:.2f}" y="{yy}" width="{bar_width:.2f}" height="30" fill="{color}"><title>{esc(label)}: {esc(item["value"])} {esc(data["unit"])}</title></rect>',
                    f'<text x="{width - right + 16}" y="{yy + 22}" font-size="14">{item["value"]:.5g}</text>'])
    svg.append(f'<text x="28" y="{height - 28}" class="small"><title>{esc(data["source"])}</title>来源：{esc(short(data["source"], 76))}</text></svg>')
    return '\n'.join(svg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('Input and output paths must differ')
        svg = render(json.loads(args.input.read_text(encoding='utf-8')))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(svg, encoding='utf-8')
    except (ValueError, OSError) as error:
        parser.exit(2, f'Error: {error}\n')
    print(args.output)


if __name__ == '__main__':
    main()
