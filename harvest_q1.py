#!/usr/bin/env python3
"""Harvest the Q1 core corpus for the VLN survey.

Q1 is the high-precision core query defined in search_protocol.md §5.1. Scopus itself
needs an institutional key, so this runs the *same phrase set* against the three
databases that are openly queryable, and writes the result in a form that a Scopus or
Web of Science CSV export can be merged into later without redoing anything:

  OpenAlex            title_and_abstract phrase search  — the closest analogue to Scopus TITLE-ABS-KEY
  Semantic Scholar    bulk search                       — proper CS/CV conference coverage
  arXiv               ti/abs phrase search              — the preprint stream Scopus cannot see

Window: 2023-01-01 onward (PUBYEAR > 2022).

Outputs
  corpus_raw.csv         every hit, one row per (record × source), with the phrase that found it
  corpus_screening.csv   deduplicated, with empty decision columns ready for title/abstract screening
  harvest_report.json    per-source and per-phrase counts — these are the PRISMA identification numbers
"""
import json, csv, re, sys, time, urllib.parse, urllib.request, urllib.error, datetime, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
YEAR_FROM = 2023
UA = {"User-Agent": "gtu-vln-survey-harvester/1.0"}

# ── Q1, verbatim from search_protocol.md §5.1 ────────────────────────────────
PHRASES = [
    "vision-and-language navigation",
    "vision language navigation",
    "vision-language navigation",
    "language-guided navigation",
    "language guided navigation",
    "language-driven navigation",
    "language-conditioned navigation",
    "instruction-following navigation",
    "instruction following navigation",
    "natural language navigation",
    "text-guided navigation",
]

def log(*a): print(*a, file=sys.stderr, flush=True)

def get(url, tries=5, data=None, hdr=None):
    h = dict(UA); h.update(hdr or {})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r) if 'json' in r.headers.get('Content-Type', 'json') else r.read()
        except urllib.error.HTTPError as e:
            w = 12 * (i + 1) if e.code in (429, 503) else 5
            log(f"      HTTP {e.code} -> sleep {w}s"); time.sleep(w)
        except Exception as e:
            log(f"      {type(e).__name__}: {e} -> sleep 8s"); time.sleep(8)
    return None

def norm_title(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())

def blank():
    return {"title": "", "abstract": "", "year": None, "venue": "", "doi": "", "arxiv": "",
            "authors": "", "n_authors": 0, "citations": None, "url": "", "type": "",
            "sources": set(), "phrases": set(), "oa": False}

# ── OpenAlex ─────────────────────────────────────────────────────────────────
def openalex(phrase):
    out, cursor, page = [], "*", 0
    while cursor and page < 12:
        f = f'title_and_abstract.search:"{phrase}",from_publication_date:{YEAR_FROM}-01-01'
        u = ("https://api.openalex.org/works?filter=" + urllib.parse.quote(f, safe=':,"') +
             f"&per-page=200&cursor={urllib.parse.quote(cursor)}")
        d = get(u)
        if not d: break
        for w in d.get("results", []):
            r = blank()
            r["title"] = w.get("display_name") or ""
            ab = w.get("abstract_inverted_index")
            if ab:
                pos = {}
                for word, idxs in ab.items():
                    for i in idxs: pos[i] = word
                r["abstract"] = " ".join(pos[k] for k in sorted(pos))[:1500]
            r["year"] = w.get("publication_year")
            loc = (w.get("primary_location") or {}) or {}
            r["venue"] = (((loc.get("source") or {}) or {}).get("display_name") or "").strip()
            r["doi"] = (w.get("doi") or "").replace("https://doi.org/", "")
            for l in (w.get("locations") or []):
                m = re.search(r'arxiv\.org/abs/([0-9]+\.[0-9]+)', l.get("landing_page_url") or "")
                if m: r["arxiv"] = m.group(1); break
            au = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
            r["authors"] = "; ".join([a for a in au[:4] if a]) + (" et al." if len(au) > 4 else "")
            r["n_authors"] = len(au)
            r["citations"] = w.get("cited_by_count")
            r["url"] = (w.get("ids") or {}).get("openalex", "")
            r["type"] = w.get("type") or ""
            r["oa"] = bool((w.get("open_access") or {}).get("is_oa"))
            r["sources"].add("openalex"); r["phrases"].add(phrase)
            out.append(r)
        cursor = (d.get("meta") or {}).get("next_cursor")
        page += 1
        time.sleep(1.1)
    return out

# ── Semantic Scholar bulk search ─────────────────────────────────────────────
def s2_bulk():
    q = " | ".join(f'"{p}"' for p in PHRASES)
    fields = ("title,abstract,year,venue,publicationVenue,citationCount,externalIds,authors,"
              "publicationTypes,url,openAccessPdf")
    out, token, page = [], None, 0
    while page < 12:
        u = ("https://api.semanticscholar.org/graph/v1/paper/search/bulk?"
             f"query={urllib.parse.quote(q)}&year={YEAR_FROM}-&fields={fields}")
        if token: u += f"&token={urllib.parse.quote(token)}"
        d = get(u)
        if not d: break
        for p in d.get("data", []) or []:
            r = blank()
            r["title"] = p.get("title") or ""
            r["abstract"] = (p.get("abstract") or "")[:1500]
            r["year"] = p.get("year")
            pv = (p.get("publicationVenue") or {}) or {}
            r["venue"] = (pv.get("name") or p.get("venue") or "").strip()
            ext = p.get("externalIds") or {}
            r["doi"] = ext.get("DOI", "") or ""
            r["arxiv"] = ext.get("ArXiv", "") or ""
            au = [a.get("name", "") for a in (p.get("authors") or [])]
            r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
            r["n_authors"] = len(au)
            r["citations"] = p.get("citationCount")
            r["url"] = p.get("url", "")
            r["type"] = ",".join(p.get("publicationTypes") or [])
            r["oa"] = bool(p.get("openAccessPdf"))
            r["sources"].add("s2")
            low = (r["title"] + " " + r["abstract"]).lower()
            r["phrases"] = {ph for ph in PHRASES if ph in low} or {"(s2 bulk)"}
            out.append(r)
        token = d.get("token")
        page += 1
        if not token: break
        time.sleep(2)
    return out

# ── arXiv ────────────────────────────────────────────────────────────────────
def arxiv():
    import xml.etree.ElementTree as ET
    NS = {'a': 'http://www.w3.org/2005/Atom'}
    out = []
    for i in range(0, len(PHRASES), 4):
        chunk = PHRASES[i:i + 4]
        q = " OR ".join(f'abs:"{p}" OR ti:"{p}"' for p in chunk)
        start = 0
        while start < 400:
            u = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q) +
                 f"&start={start}&max_results=100&sortBy=submittedDate&sortOrder=descending")
            raw = get(u)
            if raw is None: break
            try: root = ET.fromstring(raw if isinstance(raw, bytes) else json.dumps(raw).encode())
            except Exception as e: log(f"      arXiv parse: {e}"); break
            entries = root.findall('a:entry', NS)
            if not entries: break
            for e in entries:
                pub = (e.find('a:published', NS).text or "")[:4]
                if not pub.isdigit() or int(pub) < YEAR_FROM: continue
                r = blank()
                r["title"] = re.sub(r'\s+', ' ', (e.find('a:title', NS).text or '')).strip()
                r["abstract"] = re.sub(r'\s+', ' ', (e.find('a:summary', NS).text or ''))[:1500]
                r["year"] = int(pub)
                r["venue"] = "arXiv (preprint)"
                r["arxiv"] = e.find('a:id', NS).text.rsplit('/', 1)[-1].split('v')[0]
                doi_el = e.find('a:doi', {'a': 'http://arxiv.org/schemas/atom'})
                r["doi"] = (doi_el.text if doi_el is not None else "") or ""
                au = [a.find('a:name', NS).text for a in e.findall('a:author', NS)]
                r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
                r["n_authors"] = len(au)
                r["url"] = f"https://arxiv.org/abs/{r['arxiv']}"
                r["type"] = "preprint"; r["oa"] = True
                r["sources"].add("arxiv")
                low = (r["title"] + " " + r["abstract"]).lower()
                r["phrases"] = {ph for ph in chunk if ph in low} or set(chunk[:1])
                out.append(r)
            if len(entries) < 100: break
            start += 100
            time.sleep(3.2)
        time.sleep(3.2)
    return out

# ── harvest ──────────────────────────────────────────────────────────────────
report = {"query": "Q1 core (search_protocol.md §5.1)", "window": f"{YEAR_FROM}-01-01 onward",
          "retrieved": datetime.date.today().isoformat(), "phrases": PHRASES,
          "per_source": {}, "per_phrase": {}, "note":
          "Scopus and Web of Science require institutional credentials and are not included; "
          "export them separately and merge on DOI / normalised title."}
allhits = []

log("── OpenAlex ──")
oa_hits = []
for p in PHRASES:
    h = openalex(p)
    log(f"  {p:<36} {len(h)}")
    report["per_phrase"][p] = len(h)
    oa_hits += h
allhits += oa_hits
report["per_source"]["openalex"] = len(oa_hits)

log("── Semantic Scholar (bulk) ──")
s2_hits = s2_bulk()
log(f"  {len(s2_hits)} records")
allhits += s2_hits
report["per_source"]["semantic_scholar"] = len(s2_hits)

log("── arXiv ──")
ax_hits = arxiv()
log(f"  {len(ax_hits)} records")
allhits += ax_hits
report["per_source"]["arxiv"] = len(ax_hits)

report["raw_records"] = len(allhits)
log(f"\nraw identification: {len(allhits)}")

# ── deduplicate: DOI → arXiv id → normalised title ───────────────────────────
merged, key_of = {}, {}
def keyfor(r):
    if r["doi"]:
        k = "doi:" + r["doi"].lower()
        if k in merged: return k
    if r["arxiv"]:
        k = "arx:" + r["arxiv"]
        if k in merged: return k
    k = "ttl:" + norm_title(r["title"])
    if k in merged: return k
    return ("doi:" + r["doi"].lower()) if r["doi"] else \
           ("arx:" + r["arxiv"]) if r["arxiv"] else k

for r in allhits:
    if not r["title"]: continue
    k = keyfor(r)
    if k not in merged:
        merged[k] = r
    else:
        m = merged[k]
        m["sources"] |= r["sources"]; m["phrases"] |= r["phrases"]
        for f in ("doi", "arxiv", "venue", "abstract", "authors", "url", "type"):
            if not m[f] and r[f]: m[f] = r[f]
        if m["year"] is None: m["year"] = r["year"]
        if (r["citations"] or 0) > (m["citations"] or 0): m["citations"] = r["citations"]
        m["oa"] = m["oa"] or r["oa"]
        if m["n_authors"] < r["n_authors"]:
            m["authors"], m["n_authors"] = r["authors"], r["n_authors"]

# a second pass collapses arXiv/published pairs that only match on title
by_title = defaultdict(list)
for k, r in merged.items(): by_title[norm_title(r["title"])].append(k)
for t, ks in by_title.items():
    if len(ks) < 2 or not t: continue
    ks.sort(key=lambda k: (merged[k]["venue"] == "arXiv (preprint)", -(merged[k]["citations"] or 0)))
    keep = ks[0]
    for k in ks[1:]:
        r = merged.pop(k)
        m = merged[keep]
        m["sources"] |= r["sources"]; m["phrases"] |= r["phrases"]
        for f in ("doi", "arxiv", "venue", "abstract", "authors", "url"):
            if not m[f] and r[f]: m[f] = r[f]
        if (r["citations"] or 0) > (m["citations"] or 0): m["citations"] = r["citations"]

recs = sorted(merged.values(), key=lambda r: -(r["citations"] or -1))
report["after_dedup"] = len(recs)
report["duplicates_removed"] = len(allhits) - len(recs)
report["multi_source"] = sum(1 for r in recs if len(r["sources"]) > 1)
report["preprint_only"] = sum(1 for r in recs if r["venue"] == "arXiv (preprint)")
log(f"after dedup: {len(recs)}  (removed {report['duplicates_removed']})")

# ── write ────────────────────────────────────────────────────────────────────
RAW = ["title", "year", "venue", "authors", "n_authors", "doi", "arxiv", "citations",
       "type", "oa", "url", "sources", "phrases", "abstract"]
with open(os.path.join(HERE, "corpus_raw.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(RAW)
    for r in allhits:
        w.writerow([r["title"], r["year"], r["venue"], r["authors"], r["n_authors"], r["doi"],
                    r["arxiv"], r["citations"], r["type"], r["oa"], r["url"],
                    "|".join(sorted(r["sources"])), "|".join(sorted(r["phrases"])), r["abstract"]])

SCREEN = RAW + ["decision", "reason_code", "supervision", "zs_claim", "task", "llm_role",
                "observation", "scene_repr", "benchmark", "sr", "spl", "real_robot",
                "code_available", "notes"]
with open(os.path.join(HERE, "corpus_screening.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(SCREEN)
    for r in recs:
        w.writerow([r["title"], r["year"], r["venue"], r["authors"], r["n_authors"], r["doi"],
                    r["arxiv"], r["citations"], r["type"], r["oa"], r["url"],
                    "|".join(sorted(r["sources"])), "|".join(sorted(r["phrases"])), r["abstract"]]
                   + [""] * (len(SCREEN) - len(RAW)))

json.dump(report, open(os.path.join(HERE, "harvest_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
log("\nDONE " + json.dumps({k: v for k, v in report.items()
                            if k in ("raw_records", "after_dedup", "duplicates_removed",
                                     "multi_source", "preprint_only", "per_source")}))
