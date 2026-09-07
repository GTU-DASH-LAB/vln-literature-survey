#!/usr/bin/env python3
"""Fetch the untruncated abstract for every paper on the reading list.

corpus_screening.csv caps abstracts at 1500 characters, which is where the harvesters
cut them. Writing a survey off a truncated abstract loses exactly the part that matters
-- the results sentence at the end. This re-fetches the full text of the abstract from
arXiv (for the 84 with an arXiv id) and Semantic Scholar (for the rest), and writes
data/reading_notes.json: one record per paper, with the full abstract and the fields the
survey's tables need.

This is abstract-level evidence, not full text. Every claim written from it is a claim
the abstract itself makes. Numbers that live in a paper's results table are NOT here and
must not be invented -- they are marked as extraction slots in the manuscript.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "gtu-vln-survey/1.0"}
NS = {'a': 'http://www.w3.org/2005/Atom'}

def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            time.sleep(min(60, 8 * 2 ** i)); print(f"  HTTP {e.code}", file=sys.stderr)
        except Exception as e:
            time.sleep(6); print(f"  {type(e).__name__}", file=sys.stderr)
    return None

def clean(t):
    return re.sub(r'\s+', ' ', t or '').strip()

csv.field_size_limit(10_000_000)
rl = json.load(open(os.path.join(DATA, "reading_list.json"), encoding="utf-8"))
rows = rl["rows"]

# reading_list.json caps abstracts at 420 chars for the web page; the screening
# corpus holds 1500. Use the longer one as the fallback, never the page's copy.
_scr = {r["title"]: (r.get("abstract") or "")
        for r in csv.DictReader(open(os.path.join(DATA, "corpus_screening.csv"), encoding="utf-8"))}
for r in rows:
    if len(_scr.get(r["title"], "")) > len(r.get("abstract") or ""):
        r["abstract"] = _scr[r["title"]]
by_arxiv = {r["arxiv"]: r for r in rows if r.get("arxiv")}
print(f"{len(rows)} papers; {len(by_arxiv)} with arXiv ids", file=sys.stderr)

# ── arXiv, 40 ids per call ───────────────────────────────────────────────────
got = {}
ids = list(by_arxiv)
for i in range(0, len(ids), 40):
    chunk = ids[i:i + 40]
    raw = get("http://export.arxiv.org/api/query?id_list=" + ",".join(chunk) + "&max_results=40")
    if not raw:
        print(f"  !! arXiv batch {i} failed", file=sys.stderr); continue
    for e in ET.fromstring(raw).findall('a:entry', NS):
        aid = e.find('a:id', NS).text.rsplit('/', 1)[-1].split('v')[0]
        got[aid] = {"abstract": clean(e.find('a:summary', NS).text),
                    "title": clean(e.find('a:title', NS).text),
                    "categories": [c.get('term') for c in
                                   e.findall('{http://www.w3.org/2005/Atom}category')],
                    "abstract_source": "arxiv"}
    print(f"  arXiv {i}-{i+len(chunk)}: {len(got)} total", file=sys.stderr)
    time.sleep(3.2)

# ── Semantic Scholar batch for whatever is left ──────────────────────────────
missing = [r for r in rows if r.get("arxiv") not in got]
if missing:
    ids2, idx = [], {}
    for r in missing:
        k = f"ARXIV:{r['arxiv']}" if r.get("arxiv") else (f"DOI:{r['doi']}" if r.get("doi") else None)
        if k: idx[k] = r; ids2.append(k)
    if ids2:
        req = urllib.request.Request(
            "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,abstract,venue,year",
            data=json.dumps({"ids": ids2}).encode(), headers={**UA, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as rsp:
                for k, p in zip(ids2, json.load(rsp)):
                    if p and p.get("abstract"):
                        idx[k]["_s2abs"] = clean(p["abstract"])
        except Exception as e:
            print(f"  !! S2 batch: {type(e).__name__}: {e}", file=sys.stderr)

# ── assemble ─────────────────────────────────────────────────────────────────
out, stats = [], {"arxiv": 0, "s2": 0, "truncated": 0}
for r in rows:
    a = got.get(r.get("arxiv") or "", {})
    if a.get("abstract"):
        abstract, src = a["abstract"], "arxiv"; stats["arxiv"] += 1
    elif r.get("_s2abs"):
        abstract, src = r.pop("_s2abs"), "s2"; stats["s2"] += 1
    else:
        abstract, src = r.get("abstract", ""), "corpus"; stats["truncated"] += 1
    out.append({k: r.get(k) for k in
                ("rank", "tier", "is_seed", "title", "year", "venue", "citations",
                 "cites_per_year", "doi", "arxiv", "url", "query_sets", "sources")}
               | {"abstract": abstract, "abstract_source": src,
                  "abstract_chars": len(abstract),
                  "arxiv_categories": a.get("categories", [])})

json.dump({"n": len(out), "abstract_sources": stats,
           "note": "Abstract-level evidence. Results-table numbers are not here.",
           "rows": out}, open(os.path.join(DATA, "reading_notes.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n-> data/reading_notes.json  {stats}", file=sys.stderr)
