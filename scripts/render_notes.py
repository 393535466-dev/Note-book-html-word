#!/usr/bin/env python3
"""Render plain-text learning notes JSON to a standalone HTML file (stdlib only)."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit


def string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a nonempty string')
    return value


def esc(value):
    return html.escape(value, quote=True).replace('\n', '<br>')


def text_list(value, field):
    if not isinstance(value, list):
        raise ValueError(f'{field} must be a list')
    return [string(item, field) for item in value]


def table_html(table):
    if not isinstance(table, dict):
        raise ValueError('table must be an object')
    caption = string(table.get('caption'), 'table.caption')
    columns = text_list(table.get('columns'), 'table.columns')
    rows = table.get('rows')
    if not columns or not isinstance(rows, list) or not rows:
        raise ValueError('table requires columns and nonempty rows')
    badges = {'重点': 'priority', '次要': 'secondary', '了解即可': 'background'}
    body = []
    for row in rows:
        cells = text_list(row, 'table row')
        if len(cells) != len(columns):
            raise ValueError('table row length must match columns')
        rendered = []
        for cell in cells:
            content = esc(cell)
            if cell in badges:
                content = f'<span class="badge {badges[cell]}">{content}</span>'
            rendered.append(f'<td>{content}</td>')
        body.append('<tr>' + ''.join(rendered) + '</tr>')
    return ('<div class="table-wrap"><table><caption>' + esc(caption) + '</caption><thead><tr>'
            + ''.join('<th scope="col">' + esc(c) + '</th>' for c in columns)
            + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>')


def block_html(block):
    if not isinstance(block, dict):
        raise ValueError('section must be an object')
    parts = []
    if 'intro' in block:
        parts.append('<p class="note">' + esc(string(block['intro'], 'intro')) + '</p>')
    for paragraph in text_list(block.get('paragraphs', []), 'paragraphs'):
        parts.append('<p>' + esc(paragraph) + '</p>')
    for key, tag in [('bullets', 'ul'), ('steps', 'ol')]:
        items = text_list(block.get(key, []), key)
        if items:
            parts.append(f'<{tag}>' + ''.join('<li>' + esc(i) + '</li>' for i in items) + f'</{tag}>')
    if 'table' in block:
        parts.append(table_html(block['table']))
    if not parts:
        raise ValueError('section must contain content')
    return ''.join(parts)


def render_notes(data):
    if not isinstance(data, dict):
        raise ValueError('notes must be an object')
    title = string(data.get('title'), 'title')
    summary = string(data.get('summary'), 'summary')
    sections = data.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError('sections must be a nonempty list')
    if not any(isinstance(s, dict) and 'table' in s for s in sections):
        raise ValueError('at least one main section must contain a table')
    parts = ['<header>']
    if 'meta' in data:
        parts.append('<p class="meta">' + esc(string(data['meta'], 'meta')) + '</p>')
    parts.extend(['<h1>' + esc(title) + '</h1>', '<p class="lead">' + esc(summary) + '</p></header>'])
    highlights = text_list(data.get('highlights', []), 'highlights')
    if highlights:
        parts.append('<section><h2>先记住这几件事</h2><ul class="highlights">'
                     + ''.join('<li>' + esc(i) + '</li>' for i in highlights) + '</ul></section>')
    navigation = []
    rendered = []
    for i, section in enumerate(sections, 1):
        heading = string(section.get('title') if isinstance(section, dict) else None, 'section.title')
        navigation.append(f'<a href="#section-{i}">' + esc(heading) + '</a>')
        rendered.append(f'<section id="section-{i}"><h2>' + esc(heading) + '</h2>' + block_html(section) + '</section>')
    parts.append('<nav aria-label="笔记目录">' + ''.join(navigation) + '</nav>')
    parts.extend(rendered)
    questions = data.get('questions', [])
    if not isinstance(questions, list):
        raise ValueError('questions must be a list')
    if questions:
        parts.append('<section><h2>遮住答案，试着回答</h2><p class="note">先回答，再展开核对。</p>')
        for q in questions:
            if not isinstance(q, dict):
                raise ValueError('question must be an object')
            parts.append('<details><summary>' + esc(string(q.get('question'), 'question')) + '</summary>'
                         + '<div class="answer">' + esc(string(q.get('answer'), 'answer')) + '</div></details>')
        parts.append('</section>')
    appendices = data.get('appendices', [])
    if not isinstance(appendices, list):
        raise ValueError('appendices must be a list')
    if appendices:
        parts.append('<section><h2>按需展开</h2>')
        for appendix in appendices:
            heading = string(appendix.get('title') if isinstance(appendix, dict) else None, 'appendix.title')
            parts.append('<details><summary>' + esc(heading) + '</summary><div class="detail-body">'
                         + block_html(appendix) + '</div></details>')
        parts.append('</section>')
    sources = data.get('sources', [])
    if not isinstance(sources, list):
        raise ValueError('sources must be a list')
    if sources:
        parts.append('<details><summary>外部核实来源</summary><div class="detail-body"><ul>')
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError('source must be an object')
            url = string(source.get('url'), 'source.url')
            parsed = urlsplit(url)
            if parsed.scheme not in ('https', 'http') or not parsed.netloc or any(c.isspace() for c in url):
                raise ValueError('source URL must use HTTP(S) without whitespace')
            parts.append('<li><a href="' + html.escape(url, quote=True) + '" target="_blank" rel="noopener noreferrer">'
                         + esc(string(source.get('label'), 'source.label')) + '</a></li>')
        parts.append('</ul></div></details>')
    if 'review' in data:
        parts.append('<p class="review">' + esc(string(data['review'], 'review')) + '</p>')
    parts.append('<footer>重点分级为整理建议；补充与待确认项以页面标记为准。可离线阅读，浏览器打印可查看完整问答与附录。</footer>')
    template = (Path(__file__).resolve().parent.parent / 'assets' / 'notes-template.html').read_text(encoding='utf-8')
    return template.replace('{{TITLE}}', html.escape(title)).replace('{{BODY}}', ''.join(parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        output = render_notes(json.loads(args.input.read_text(encoding='utf-8')))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('w' if args.overwrite else 'x', encoding='utf-8') as handle:
            handle.write(output)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'Cannot render notes: {exc}\n')
    print(f'Created {args.output.resolve()}')


if __name__ == '__main__':
    main()
