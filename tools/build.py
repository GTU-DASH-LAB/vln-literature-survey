#!/usr/bin/env python3
"""Build index.html from the template, the inlined fonts and the seed corpus.

The page is deliberately self-contained: no external requests, no CDN, fonts embedded
as woff2 data URIs. Edit build/page.template.html — never index.html.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
p = lambda *a: os.path.join(DATA, *a)
site = lambda *a: os.path.join(ROOT, "site", *a)

KEEP = ['group', 'short', 'supervision', 'zs_claim', 'task', 'section', 'title', 'year',
        'venue', 's2_venue', 'citations_primary', 'citations_source', 'oa_citations',
        'authors', 'doi', 'arxiv', 'openalex', 's2_url', 'abstract', 'match_score', 'resolved']

def load(name):
    """Harvest outputs are optional — the page renders without them."""
    try:
        return json.load(open(p(name), encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return None

tpl = open(site('page.template.html'), encoding='utf-8').read()
fonts = open(site('fonts.css'), encoding='utf-8').read()
data = json.load(open(p('corpus_seeds.json'), encoding='utf-8'))

payload = {'meta': data['meta'], 'rows': [{k: r.get(k) for k in KEEP} for r in data['rows']]}
# the harvest numbers are injected, never typed into the template: rebuild after every run
harvest = {'report': load('harvest_report.json'), 'audit': load('recall_audit.json')}
reading = load('reading_list.json')

# the screening corpus itself, trimmed for the browser: abstracts are 3.3 MB in full
CORPUS_KEEP = ['title', 'year', 'venue', 'citations', 'doi', 'arxiv', 'url', 'sources',
               'query_sets', 'decision', 'reason_code', 'task', 'zs_claim']
def load_corpus():
    import csv
    csv.field_size_limit(10_000_000)
    try:
        rows = list(csv.DictReader(open(p('corpus_screening.csv'), encoding='utf-8')))
    except FileNotFoundError:
        return []
    out = []
    for r in rows:
        d = {k: (r.get(k) or '') for k in CORPUS_KEEP}
        d['abstract'] = (r.get('abstract') or '')[:420]
        out.append(d)
    return out
corpus = load_corpus()
def scope_css(css, scope):
    """Prefix every selector in a stylesheet with `scope`.

    Inlining an SVG drops its <style> into the page's global CSS scope, and this
    figure's class names are one and two letters (.n, .ar, .t) — two of which the
    page already uses. Prefixing keeps the figure from restyling the document.
    Handles @media by recursing into the block.
    """
    def sel(s):
        out = []
        for part in (x.strip() for x in s.split(',')):
            if not part:
                continue
            # :root[data-theme] must stay at the root; the scope goes after it
            m = re.match(r'^(:root\[[^\]]*\])\s*(.*)$', part)
            out.append(f'{m.group(1)} {scope} {m.group(2)}'.strip() if m
                       else f'{scope} {part}')
        return ', '.join(out)

    out, i = [], 0
    while i < len(css):
        b = css.find('{', i)
        if b < 0:
            break
        head, d, k = css[i:b].strip(), 1, b + 1
        while k < len(css) and d:                       # brace-match the block
            d += (css[k] == '{') - (css[k] == '}')
            k += 1
        body = css[b + 1:k - 1]
        out.append(f'{head}{{{scope_css(body, scope)}}}' if head.startswith('@')
                   else f'{sel(head)}{{{body}}}')
        i = k
    return '\n'.join(out)

# the flow diagram is generated from the harvest logs by make_flow_diagram.py;
# inline it so the page stays a single self-contained file
flow = open(site('fig', 'selection-flow.svg'), encoding='utf-8').read()
a, b = flow.index('<style>') + 7, flow.index('</style>')
flow = flow[:a] + scope_css(flow[a:b], '.flowfig') + flow[b:]

out = (tpl.replace('<!--FLOWSVG-->', flow)
          .replace('/*FONTS*/', fonts)
          .replace('/*DATA*/', json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
          .replace('/*HARVEST*/', json.dumps(harvest, ensure_ascii=False, separators=(',', ':')))
          .replace('/*CORPUS*/', json.dumps(corpus, ensure_ascii=False, separators=(',', ':')))
          .replace('/*READING*/', json.dumps(reading, ensure_ascii=False, separators=(',', ':'))))

open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(out)
hv = "harvest+audit" if harvest['report'] and harvest['audit'] else "no harvest data"
print(f"index.html  {len(out)/1024:.0f} KB  ({len(payload['rows'])} seeds, "
      f"{len(corpus)} corpus records, {hv})")
