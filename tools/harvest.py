#!/usr/bin/env python3
"""Harvest the screening corpus for the VLN survey.

Runs four query sets (search_protocol.md §5) against the queryable databases, then deduplicates across all of them:

  core      Q1 — the "...navigation" phrase family. High precision.
  recall    Q2/Q4 — the other names this field gives the task: visual language
            navigation, object goal navigation, embodied navigation. Q1 alone
            recovered only 8/35 seed works; this set exists because of that.
  zeroshot  Q5 — zero-shot / training-free / open-vocabulary navigation. Tagged
            separately, low precision expected.
  enabler   Open-vocabulary maps, 3D scene graphs and code-as-policy. These never
            say "navigation" but Sections 6.5, 9.3 and 9.6 depend on them.

  OpenAlex          title_and_abstract phrase search - closest analogue to Scopus TITLE-ABS-KEY
  Semantic Scholar  bulk search - proper CS/CV conference coverage
  arXiv             ti/abs phrase search - the preprint stream Scopus cannot see
  IEEE Xplore       CVPR/ICCV/WACV, ICRA, IROS, RA-L, T-RO - the densest venues for this
                    topic. Needs IEEE_API_KEY (developer.ieee.org, free on academic
                    request); the source is skipped when the key is absent
  Crossref          DOI metadata for IEEE, ACM, Springer and Elsevier - the keyless
                    stand-in for the publisher databases; fuzzy search, so hits are
                    re-checked for the phrase before they are kept
  DBLP              title search over the canonical CS venue index; no abstracts, but it
                    catches published versions the others still hold as preprints
  OpenReview        notes/search on both API hosts - NeurIPS/ICLR/ICML/CoRL, the
                    venues neither Scopus nor WoS index (protocol §5.6)

Scopus and Web of Science need an institutional session and are merged from an export
instead - see merge_export.py.

Window: 2023-01-01 onward (PUBYEAR > 2022).

  python3 tools/harvest.py                        # all four sets, adding to what is already on file
  python3 tools/harvest.py core                   # one set
  python3 tools/harvest.py --only openalex        # one source, e.g. after it rate-limited you
  python3 tools/harvest.py --fresh                # discard data/corpus_raw.csv and start the log over
  python3 tools/harvest.py --rebuild              # rebuild the corpus and report from the log, query nothing

data/corpus_raw.csv is an append-only identification log: each block of hits is written the moment
it is collected, and every run rebuilds the deduplicated corpus and the report from the whole
file. A killed run, or one whose source was rate-limited, therefore costs nothing - re-run the
set, or just the missing source with --only, and the rows are added to what is already there.

Outputs
  data/corpus_raw.csv         every hit, one row per (record x source), with query set and phrase
  data/corpus_screening.csv   deduplicated, with empty decision columns ready for screening
  data/harvest_report.json    per-set, per-source and per-phrase counts - the PRISMA identification numbers

Scopus and Web of Science need an institutional session and are not harvested here.
Export them separately and merge on DOI / normalised title; the output is shaped so
that merge is a straight append.
"""
import json, csv, re, sys, time, urllib.parse, urllib.request, urllib.error, datetime, os
from collections import defaultdict

# ponytail: python.org macOS builds ship no CA bundle; certifi is already installed with them
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
YEAR_FROM = 2023
UA = {"User-Agent": "gtu-vln-survey-harvester/1.0"}
# OpenAlex rate-limits the anonymous pool hard. Set OPENALEX_MAILTO=you@example.org to join
# the polite pool, which is what stops the 429 storms on a full four-set run.
MAILTO = os.environ.get("OPENALEX_MAILTO", "").strip()
# IEEE Xplore needs a key: developer.ieee.org, free on academic request. Never put it in the
# repo - this one is public. Export IEEE_API_KEY instead. The free tier is a few hundred calls
# a day, which is why this source pages less deeply than the others.
IEEE_KEY = os.environ.get("IEEE_API_KEY", "").strip()

# ── Query sets (search_protocol.md §5) ─────────────────────────────
QUERY_SETS = {
    # Q1 core, verbatim from §5.1
    "core": [
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
    ],
    # Q2/Q4 recall — the other names the field uses for the same task
    "recall": [
        "visual language navigation",
        "visual-language navigation",
        "object goal navigation",
        "object-goal navigation",
        "objectgoal navigation",
        "object navigation",
        "embodied navigation",
        "instruction navigation",
        "semantic navigation",
        "visual target navigation",      # L3MVN's title phrase — §5.8 audit miss
        "lifelong navigation",           # GOAT-Bench — §5.8 audit miss
        "multimodal navigation",
        "multi-modal navigation",
        "demand-driven navigation",
        "remote object grounding",
        "vision-language-action model",
    ],
    # Q5 zero-shot axis — tagged separately, low precision expected
    "zeroshot": [
        "zero-shot navigation",
        "zero shot navigation",
        "training-free navigation",
        "open-vocabulary navigation",
        "open vocabulary navigation",
        "zero-shot object navigation",
        "zero-shot object goal navigation",
        "language-grounded robot navigation",
    ],
    # §6.5 / 9.3 / 9.6 enablers — these papers never say "navigation"
    "enabler": [
        "open-vocabulary map",
        "visual language map",
        "open-vocabulary scene graph",
        "open-vocabulary 3d scene graph",
        "queryable scene representation",
        "open-set 3d mapping",
        "multimodal 3d mapping",         # ConceptFusion says "open-set multimodal 3D mapping"
        "code as policies",
        "language model programs",
    ],
}

SOURCES = ("openalex", "crossref", "ieee", "semantic_scholar", "arxiv", "dblp", "openreview")
RAW = ["title", "year", "venue", "authors", "n_authors", "doi", "arxiv", "citations",
       "type", "oa", "url", "sources", "query_sets", "phrases", "abstract"]
RAW_PATH = os.path.join(DATA, "corpus_raw.csv")

def log(*a): print(*a, file=sys.stderr, flush=True)

# requests that exhausted their retries; a phrase that hit one has an unknown count,
# not a zero, and the report has to say so or the PRISMA figures are wrong
FAILED = []

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
    log(f"      GAVE UP after {tries} tries: {url[:110]}")
    FAILED.append(url)
    return None

def norm_title(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())

def blank():
    return {"title": "", "abstract": "", "year": None, "venue": "", "doi": "", "arxiv": "",
            "authors": "", "n_authors": 0, "citations": None, "url": "", "type": "",
            "sources": set(), "phrases": set(), "qsets": set(), "oa": False}

# ── OpenAlex ─────────────────────────────────────────────────────────────────
def openalex(phrase, qset):
    out, cursor, page = [], "*", 0
    while cursor and page < 12:
        f = f'title_and_abstract.search:"{phrase}",from_publication_date:{YEAR_FROM}-01-01'
        u = ("https://api.openalex.org/works?filter=" + urllib.parse.quote(f, safe=':,"') +
             f"&per-page=200&cursor={urllib.parse.quote(cursor)}" +
             (f"&mailto={urllib.parse.quote(MAILTO)}" if MAILTO else ""))
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
            r["sources"].add("openalex"); r["phrases"].add(phrase); r["qsets"].add(qset)
            out.append(r)
        cursor = (d.get("meta") or {}).get("next_cursor")
        page += 1
        time.sleep(1.1)
    return out


# ── Crossref (§3 Tier 1 by proxy — IEEE, ACM, Springer and Elsevier DOIs) ────
# The keyless stand-in for the publisher databases: Crossref holds the DOI metadata
# IEEE Xplore, the ACM DL and SpringerLink deposit. Its search is fuzzy, so every hit is
# re-checked for the phrase before it is kept.
def crossref(phrase, qset):
    # offset paging, not cursor: a cursor scan drops the relevance ordering, and without it
    # the first page is effectively random. Relevance decays fast, so five pages is the tail.
    out = []
    for offset in range(0, 500, 100):
        u = ("https://api.crossref.org/works?query.bibliographic=" + urllib.parse.quote(f'"{phrase}"') +
             f"&filter=from-pub-date:{YEAR_FROM}-01-01,type:journal-article,type:proceedings-article"
             f"&rows=100&offset={offset}" +
             (f"&mailto={urllib.parse.quote(MAILTO)}" if MAILTO else ""))
        d = get(u)
        msg = (d or {}).get("message") or {}
        items = msg.get("items") or []
        if not items: break
        for it in items:
            title = " ".join(it.get("title") or []).strip()
            abstract = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
            abstract = re.sub(r"\s+", " ", abstract).strip()
            venue = " ".join(it.get("container-title") or []).strip()
            if phrase not in (title + " " + abstract + " " + venue).lower(): continue
            parts = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
            year = parts[0] if parts and isinstance(parts[0], int) else None
            if not year or year < YEAR_FROM: continue
            r = blank()
            r["title"] = re.sub(r"\s+", " ", title)
            r["abstract"] = abstract[:1500]
            r["year"] = year
            r["venue"] = venue
            r["doi"] = (it.get("DOI") or "").lower()
            au = [" ".join(x for x in (a.get("given"), a.get("family")) if x)
                  for a in (it.get("author") or [])]
            au = [a for a in au if a]
            r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
            r["n_authors"] = len(au)
            r["citations"] = it.get("is-referenced-by-count")
            r["url"] = "https://doi.org/" + r["doi"] if r["doi"] else ""
            r["type"] = it.get("type") or ""
            r["sources"].add("crossref"); r["phrases"].add(phrase); r["qsets"].add(qset)
            out.append(r)
        time.sleep(1.2)
    return out

# ── DBLP (§3 Tier 2 — canonical CS venue resolution) ─────────────────────────
# Title-only search and no abstracts, but it is the cleanest index of IEEE and ACM
# conference proceedings, and it catches published versions the other sources still
# hold only as preprints.
def dblp(phrase, qset):
    out = []
    for start in (0, 1000):
        u = ("https://dblp.org/search/publ/api?q=" + urllib.parse.quote(f'"{phrase}"') +
             f"&h=1000&f={start}&format=json")
        d = get(u, tries=3)
        hits = (((d or {}).get("result") or {}).get("hits") or {}).get("hit") or []
        for h in hits:
            i = h.get("info") or {}
            title = re.sub(r"\s+", " ", (i.get("title") or "")).strip().rstrip(".")
            if phrase not in title.lower(): continue
            year = int(i["year"]) if (i.get("year") or "").isdigit() else None
            if not year or year < YEAR_FROM: continue
            r = blank()
            r["title"] = title
            r["year"] = year
            r["venue"] = (i.get("venue") if isinstance(i.get("venue"), str)
                          else " / ".join(i.get("venue") or [])) or ""
            r["doi"] = (i.get("doi") or "").lower()
            ee = i.get("ee") or ""
            m = re.search(r"arxiv\.org/abs/([0-9]+\.[0-9]+)", ee)
            if m: r["arxiv"] = m.group(1)
            a = ((i.get("authors") or {}).get("author")) or []
            if isinstance(a, dict): a = [a]
            au = [x.get("text", "") if isinstance(x, dict) else str(x) for x in a]
            au = [x for x in au if x]
            r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
            r["n_authors"] = len(au)
            r["url"] = i.get("url") or ee
            r["type"] = i.get("type") or ""
            r["sources"].add("dblp"); r["phrases"].add(phrase); r["qsets"].add(qset)
            out.append(r)
        if len(hits) < 1000: break
        time.sleep(1.5)
    time.sleep(1.5)
    return out


# ── IEEE Xplore (§3 Tier 1 — CVPR/ICCV/WACV, ICRA, IROS, RA-L, T-RO) ─────────
def ieee(phrase, qset):
    if not IEEE_KEY:
        return []
    out = []
    for start in range(1, 601, 200):            # three pages: the daily quota is small
        u = ("https://ieeexploreapi.ieee.org/api/v1/search/articles?"
             f"apikey={urllib.parse.quote(IEEE_KEY)}&format=json&max_records=200"
             f"&start_record={start}&start_year={YEAR_FROM}"
             "&querytext=" + urllib.parse.quote(f'"{phrase}"'))
        d = get(u, tries=3)
        arts = (d or {}).get("articles") or []
        if not arts: break
        for a in arts:
            title = re.sub(r"\s+", " ", (a.get("title") or "")).strip()
            abstract = re.sub(r"\s+", " ", (a.get("abstract") or "")).strip()
            venue = (a.get("publication_title") or "").strip()
            # querytext searches every field, so confirm the phrase is really in the record
            if phrase not in (title + " " + abstract).lower(): continue
            year = a.get("publication_year")
            year = int(year) if str(year).isdigit() else None
            if not year or year < YEAR_FROM: continue
            r = blank()
            r["title"] = title
            r["abstract"] = abstract[:1500]
            r["year"] = year
            r["venue"] = venue
            r["doi"] = (a.get("doi") or "").lower()
            au = [x.get("full_name", "") for x in
                  ((a.get("authors") or {}).get("authors") or []) if isinstance(x, dict)]
            au = [x for x in au if x]
            r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
            r["n_authors"] = len(au)
            r["citations"] = a.get("citing_paper_count")
            r["url"] = a.get("html_url") or (f"https://doi.org/{r['doi']}" if r["doi"] else "")
            r["type"] = (a.get("content_type") or "").strip()
            r["oa"] = (a.get("access_type") or "").lower().startswith("open")
            r["sources"].add("ieee"); r["phrases"].add(phrase); r["qsets"].add(qset)
            out.append(r)
        if len(arts) < 200: break
        time.sleep(1.5)
    time.sleep(1.5)
    return out

# ── Semantic Scholar bulk search ─────────────────────────────────────────────
def s2_bulk(phrases, qset):
    q = " | ".join(f'"{p}"' for p in phrases)
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
            r["sources"].add("s2"); r["qsets"].add(qset)
            low = (r["title"] + " " + r["abstract"]).lower()
            r["phrases"] = {ph for ph in phrases if ph in low} or {"(s2 bulk)"}
            out.append(r)
        token = d.get("token")
        page += 1
        if not token: break
        time.sleep(2)
    return out

# ── arXiv ────────────────────────────────────────────────────────────────────
def arxiv(phrases, qset):
    import xml.etree.ElementTree as ET
    NS = {'a': 'http://www.w3.org/2005/Atom'}
    out = []
    for i in range(0, len(phrases), 4):
        chunk = phrases[i:i + 4]
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
                r["sources"].add("arxiv"); r["qsets"].add(qset)
                low = (r["title"] + " " + r["abstract"]).lower()
                r["phrases"] = {ph for ph in chunk if ph in low} or set(chunk[:1])
                out.append(r)
            if len(entries) < 100: break
            start += 100
            time.sleep(3.2)
        time.sleep(3.2)
    return out


# ── OpenReview (§5.6 — the NeurIPS/ICLR/ICML/CoRL venues Scopus does not index) ─
# Two hosts: api2 serves 2024+ venues, api (v1) serves older ones plus DBLP imports.
OR_HOSTS = ("https://api2.openreview.net", "https://api.openreview.net")

def _cv(content, key):
    v = content.get(key)
    return (v or {}).get("value") if isinstance(v, dict) else (v or "")

def openreview(phrase, qset):
    out = []
    for host in OR_HOSTS:
        offset = 0
        while offset < 600:
            u = (f"{host}/notes/search?term=" + urllib.parse.quote(f'"{phrase}"') +
                 f"&limit=200&offset={offset}&source=forum")
            d = get(u, tries=3)
            notes = (d or {}).get("notes") or []
            for n in notes:
              try:
                c = n.get("content") or {}
                title = re.sub(r"\s+", " ", str(_cv(c, "title"))).strip()
                if not title: continue
                venue = str(_cv(c, "venue")) or str(_cv(c, "venueid"))
                # under-review submissions are anonymous and not peer-reviewed yet: IC2 excludes
                # them, and counting them would inflate the PRISMA identification figure
                if re.match(r"\s*submitted to", venue, re.I): continue
                bib = str(_cv(c, "_bibtex"))
                ym = re.search(r"(20[12]\d)", venue) or re.search(r"year\s*=\s*\{?(20[12]\d)", bib)
                year = int(ym.group(1)) if ym else \
                       datetime.datetime.fromtimestamp((n.get("pdate") or n.get("cdate") or 0) / 1000,
                                                       datetime.timezone.utc).year
                if year < YEAR_FROM: continue
                r = blank()
                r["title"] = title
                r["abstract"] = re.sub(r"\s+", " ", str(_cv(c, "abstract")))[:1500]
                r["year"] = year
                r["venue"] = venue.strip()
                am = re.search(r"abs-(\d{4})-(\d{4,5})", bib) or re.search(r"eprint\s*=\s*\{?(\d{4})\.(\d{4,5})", bib)
                if am: r["arxiv"] = f"{am.group(1)}.{am.group(2)}"
                dm = re.search(r"doi\s*=\s*\{([^}]+)\}", bib)
                if dm: r["doi"] = dm.group(1).replace("https://doi.org/", "").strip()
                au = _cv(c, "authors") or []
                if isinstance(au, str): au = [au]
                au = [a if isinstance(a, str) else
                      (a.get("name") or a.get("fullname") or a.get("value") or "")
                      for a in au]
                au = [a for a in au if a]
                if au == ["Anonymous"]: continue
                r["authors"] = "; ".join(au[:4]) + (" et al." if len(au) > 4 else "")
                r["n_authors"] = len(au)
                r["url"] = f"https://openreview.net/forum?id={n.get('id','')}"
                r["type"] = "conference-paper"
                r["oa"] = True
                r["sources"].add("openreview"); r["phrases"].add(phrase); r["qsets"].add(qset)
                out.append(r)
              except Exception as e:
                log(f"      skipped note {n.get('id','?')}: {type(e).__name__}: {e}")
            if len(notes) < 200: break
            offset += 200
            time.sleep(1.2)
        time.sleep(1.2)
    return out

# ── harvest ──────────────────────────────────────────────────────────────────
argv = sys.argv[1:]
REBUILD = "--rebuild" in argv        # rebuild the corpus and report from the raw log, query nothing
argv = [a for a in argv if a != "--rebuild"]
FRESH = "--fresh" in argv
argv = [a for a in argv if a != "--fresh"]
ONLY = ""
if "--only" in argv:
    i = argv.index("--only")
    ONLY = argv[i + 1] if i + 1 < len(argv) else ""
    del argv[i:i + 2]
    if ONLY not in SOURCES:
        sys.exit(f"unknown source {ONLY!r}; choose from {', '.join(SOURCES)}")
sets = argv or list(QUERY_SETS)
for q in sets:
    if q not in QUERY_SETS:
        sys.exit(f"unknown query set {q!r}; choose from {', '.join(QUERY_SETS)}")

want = lambda src: not REBUILD and (not ONLY or ONLY == src)

# data/corpus_raw.csv accumulates across runs, so a killed run or a rate-limited source costs
# nothing: re-run the affected set, or just one source with --only, and the rows are added.
if FRESH and os.path.exists(RAW_PATH):
    os.remove(RAW_PATH)
    log("--fresh: data/corpus_raw.csv removed")

def raw_key(r):
    return (norm_title(r["title"]), "|".join(sorted(r["sources"])), "|".join(sorted(r["qsets"])))

def load_raw():
    """Every row already on disk, as records."""
    if not os.path.exists(RAW_PATH): return []
    out = []
    with open(RAW_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            r = blank()
            r.update({k: row.get(k, "") for k in
                      ("title", "venue", "authors", "doi", "arxiv", "url", "type", "abstract")})
            r["year"] = int(row["year"]) if (row.get("year") or "").isdigit() else None
            r["n_authors"] = int(row["n_authors"]) if (row.get("n_authors") or "").isdigit() else 0
            r["citations"] = int(row["citations"]) if (row.get("citations") or "").isdigit() else None
            r["oa"] = row.get("oa") == "True"
            r["sources"] = set(filter(None, (row.get("sources") or "").split("|")))
            r["qsets"] = set(filter(None, (row.get("query_sets") or "").split("|")))
            r["phrases"] = set(filter(None, (row.get("phrases") or "").split("|")))
            out.append(r)
    return out

SEEN = {raw_key(r) for r in load_raw()}

def flush(rows):
    """Append this block's hits to the raw log straight away, skipping ones already logged."""
    new = [r for r in rows if r["title"] and raw_key(r) not in SEEN]
    for r in new: SEEN.add(raw_key(r))
    if not new: return 0
    exists = os.path.exists(RAW_PATH) and os.path.getsize(RAW_PATH) > 0
    with open(RAW_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if not exists: w.writerow(RAW)
        for r in new:
            w.writerow([r["title"], r["year"], r["venue"], r["authors"], r["n_authors"], r["doi"],
                        r["arxiv"], r["citations"], r["type"], r["oa"], r["url"],
                        "|".join(sorted(r["sources"])), "|".join(sorted(r["qsets"])),
                        "|".join(sorted(r["phrases"])), r["abstract"]])
    return len(new)

report = {"query_sets": sets, "window": f"{YEAR_FROM}-01-01 onward",
          "retrieved": datetime.date.today().isoformat(),
          "phrases": {q: QUERY_SETS[q] for q in sets},
          "per_source": defaultdict(int), "per_set": {}, "per_phrase": {}, "note":
          "Scopus and Web of Science require institutional credentials and are not included; "
          "export them separately and merge on DOI / normalised title."}
new_this_run = 0

for qset in sets:
    phrases = QUERY_SETS[qset]
    log(f"\n══ {qset} ({len(phrases)} phrases) ══")

    if want("openalex"):
        log("  ── OpenAlex ──")
        for p in phrases:
            before = len(FAILED)
            h = openalex(p, qset)
            incomplete = len(FAILED) > before
            added = flush(h)
            log(f"    {p:<36} {len(h)} (+{added})" +
                ("  ** INCOMPLETE, requests failed **" if incomplete else ""))
            report["per_phrase"][p] = f"{len(h)} (incomplete)" if incomplete else len(h)
            new_this_run += added

    if want("crossref"):
        log("  ── Crossref ──")
        for p in phrases:
            before = len(FAILED)
            h = crossref(p, qset)
            added = flush(h)
            log(f"    {p:<36} {len(h)} (+{added})" +
                ("  ** INCOMPLETE, requests failed **" if len(FAILED) > before else ""))
            new_this_run += added

    if want("ieee"):
        if not IEEE_KEY:
            log("  ── IEEE Xplore ── skipped: IEEE_API_KEY is not set")
        else:
            log("  ── IEEE Xplore ──")
            for p in phrases:
                before = len(FAILED)
                h = ieee(p, qset)
                added = flush(h)
                log(f"    {p:<36} {len(h)} (+{added})" +
                    ("  ** INCOMPLETE, requests failed **" if len(FAILED) > before else ""))
                new_this_run += added

    if want("semantic_scholar"):
        log("  ── Semantic Scholar (bulk) ──")
        h = s2_bulk(phrases, qset)
        added = flush(h)
        log(f"    {len(h)} records (+{added})")
        new_this_run += added

    if want("arxiv"):
        log("  ── arXiv ──")
        h = arxiv(phrases, qset)
        added = flush(h)
        log(f"    {len(h)} records (+{added})")
        new_this_run += added

    if want("dblp"):
        log("  ── DBLP ──")
        for p in phrases:
            h = dblp(p, qset)
            added = flush(h)
            log(f"    {p:<36} {len(h)} (+{added})")
            new_this_run += added

    if want("openreview"):
        log("  ── OpenReview ──")
        for p in phrases:
            h = openreview(p, qset)
            added = flush(h)
            log(f"    {p:<36} {len(h)} (+{added})")
            new_this_run += added

allhits = load_raw()
report["per_source"] = defaultdict(int)
report["per_set"] = defaultdict(int)
for r in allhits:
    for src in r["sources"]: report["per_source"][src] += 1
    for q in r["qsets"]: report["per_set"][q] += 1
report["per_source"] = dict(report["per_source"])
report["per_set"] = dict(report["per_set"])
report["new_records_this_run"] = new_this_run
report["failed_requests"] = len(FAILED)
# a rebuild queries nothing, so it must not erase the previous run's failure record
if REBUILD:
    try:
        old = json.load(open(os.path.join(DATA, "harvest_report.json"), encoding="utf-8"))
        report["per_phrase"] = old.get("per_phrase") or {}
        report["failed_requests"] = old.get("failed_requests", 0)
        report["rebuilt_from_log"] = True
    except (FileNotFoundError, ValueError):
        pass
# any source with no rows on file has simply not been harvested yet — say so rather than
# letting its absence read as "nothing found there"
report["sources_not_harvested"] = [s for s in SOURCES
                                   if s not in report["per_source"]
                                   and not (s == "semantic_scholar" and "s2" in report["per_source"])]
if FAILED:
    report["failed_request_note"] = ("Requests that exhausted their retries, nearly always a 429 from "
        "OpenAlex or OpenReview. Every phrase marked '(incomplete)' has an unknown true count, "
        "not a zero, and must be re-harvested with --only <source> before the identification "
        "numbers are reported.")
    log(f"\n!! {len(FAILED)} requests failed — per-phrase counts marked '(incomplete)' are not real zeros")


report["raw_records"] = len(allhits)
log(f"\nraw identification: {len(allhits)} rows on file (+{new_this_run} this run)")

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
        m["sources"] |= r["sources"]; m["phrases"] |= r["phrases"]; m["qsets"] |= r["qsets"]
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
        m["sources"] |= r["sources"]; m["phrases"] |= r["phrases"]; m["qsets"] |= r["qsets"]
        for f in ("doi", "arxiv", "venue", "abstract", "authors", "url"):
            if not m[f] and r[f]: m[f] = r[f]
        if (r["citations"] or 0) > (m["citations"] or 0): m["citations"] = r["citations"]

recs = sorted(merged.values(), key=lambda r: -(r["citations"] or -1))
report["after_dedup"] = len(recs)
report["duplicates_removed"] = len(allhits) - len(recs)
report["multi_source"] = sum(1 for r in recs if len(r["sources"]) > 1)
report["preprint_only"] = sum(1 for r in recs if not r["venue"] or "arxiv" in r["venue"].lower())
report["per_set_after_dedup"] = {q: sum(1 for r in recs if q in r["qsets"]) for q in sets}
log(f"after dedup: {len(recs)}  (removed {report['duplicates_removed']})")

# ── write ────────────────────────────────────────────────────────────────────
SCREEN = RAW + ["decision", "reason_code", "supervision", "zs_claim", "task", "llm_role",
                "observation", "scene_repr", "benchmark", "sr", "spl", "real_robot",
                "code_available", "notes"]
with open(os.path.join(DATA, "corpus_screening.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(SCREEN)
    for r in recs:
        w.writerow([r["title"], r["year"], r["venue"], r["authors"], r["n_authors"], r["doi"],
                    r["arxiv"], r["citations"], r["type"], r["oa"], r["url"],
                    "|".join(sorted(r["sources"])), "|".join(sorted(r["qsets"])),
                    "|".join(sorted(r["phrases"])), r["abstract"]]
                   + [""] * (len(SCREEN) - len(RAW)))

json.dump(report, open(os.path.join(DATA, "harvest_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
log("\nDONE " + json.dumps({k: v for k, v in report.items()
                            if k in ("raw_records", "after_dedup", "duplicates_removed",
                                     "multi_source", "preprint_only", "per_source", "per_set",
                                     "per_set_after_dedup")}))
