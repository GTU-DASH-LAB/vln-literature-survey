#!/usr/bin/env python3
"""Build index.html from the template, the inlined fonts and the seed corpus.

The page is deliberately self-contained: no external requests, no CDN, fonts embedded
as woff2 data URIs. Edit build/page.template.html — never index.html.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(HERE, *a)

KEEP = ['group', 'short', 'supervision', 'zs_claim', 'task', 'section', 'title', 'year',
        'venue', 's2_venue', 'citations_primary', 'citations_source', 'oa_citations',
        'authors', 'doi', 'arxiv', 'openalex', 's2_url', 'abstract', 'match_score', 'resolved']

tpl = open(p('build', 'page.template.html'), encoding='utf-8').read()
fonts = open(p('build', 'fonts.css'), encoding='utf-8').read()
data = json.load(open(p('corpus_seeds.json'), encoding='utf-8'))

payload = {'meta': data['meta'], 'rows': [{k: r.get(k) for k in KEEP} for r in data['rows']]}
out = tpl.replace('/*FONTS*/', fonts).replace(
    '/*DATA*/', json.dumps(payload, ensure_ascii=False, separators=(',', ':')))

open(p('index.html'), 'w', encoding='utf-8').write(out)
print(f"index.html  {len(out)/1024:.0f} KB  ({len(payload['rows'])} rows)")
