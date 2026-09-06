#!/usr/bin/env python3
"""Merge a Scopus or Web of Science export into the harvest corpus.

Neither database answers without an institutional session, so their records cannot be
harvested here (search_protocol.md §5.1–5.2). Run the queries in their web interfaces,
export, and hand the file to this script: it appends to `data/corpus_raw.csv` in the same
shape every other source uses, so the deduplicated corpus and the PRISMA counts are
rebuilt from one file.

  python3 tools/merge_export.py scopus.csv --set core
  python3 tools/merge_export.py savedrecs.txt --set core --source wos
  python3 tools/merge_export.py scopus.csv --set core --dry-run

Scopus: export CSV with abstracts ("Citation information + Bibliographical information +
Abstract & keywords"). Web of Science: export "Tab-delimited / Full Record".

After merging, rebuild everything downstream:

  python3 tools/harvest.py --rebuild       # recompute the corpus and report from the raw log
  python3 tools/recall_audit.py
  python3 tools/build.py
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
RAW_PATH = os.path.join(DATA, "corpus_raw.csv")
RAW = ["title", "year", "venue", "authors", "n_authors", "doi", "arxiv", "citations",
       "type", "oa", "url", "sources", "query_sets", "phrases", "abstract"]
YEAR_FROM = 2023
csv.field_size_limit(10_000_000)

# export column -> our column. Scopus ships CSV, WoS ships tab-delimited two-letter tags.
MAPS = {
    "scopus": {"title": "Title", "year": "Year", "venue": "Source title", "authors": "Authors",
               "doi": "DOI", "citations": "Cited by", "type": "Document Type",
               "url": "Link", "abstract": "Abstract"},
    "wos":    {"title": "TI", "year": "PY", "venue": "SO", "authors": "AF",
               "doi": "DI", "citations": "TC", "type": "DT", "url": "", "abstract": "AB"},
}

def norm_title(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())

def read_export(path, source):
    m = MAPS[source]
    delim = "\t" if source == "wos" else ","
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=delim))
    if rows and m["title"] not in rows[0]:
        sys.exit(f"{os.path.basename(path)} has no {m['title']!r} column — is it really a "
                 f"{source} export? Columns: {', '.join(list(rows[0])[:8])}…")
    return rows, m

def convert(rows, m, source, qset):
    out, skipped = [], 0
    for row in rows:
        title = re.sub(r"\s+", " ", (row.get(m["title"]) or "")).strip()
        ys = re.search(r"(\d{4})", row.get(m["year"]) or "")
        year = int(ys.group(1)) if ys else None
        if not title or not year or year < YEAR_FROM:
            skipped += 1
            continue
        au = [a.strip() for a in re.split(r";", row.get(m["authors"]) or "") if a.strip()]
        cited = re.sub(r"[^0-9]", "", row.get(m["citations"]) or "")
        doi = (row.get(m["doi"]) or "").strip().lower().replace("https://doi.org/", "")
        out.append({
            "title": title, "year": year,
            "venue": (row.get(m["venue"]) or "").strip(),
            "authors": "; ".join(au[:4]) + (" et al." if len(au) > 4 else ""),
            "n_authors": len(au), "doi": doi, "arxiv": "",
            "citations": int(cited) if cited else "",
            "type": (row.get(m["type"]) or "").strip(), "oa": "",
            "url": (row.get(m["url"], "") or "").strip() or ("https://doi.org/" + doi if doi else ""),
            "sources": source, "query_sets": qset, "phrases": f"({source} export)",
            "abstract": re.sub(r"\s+", " ", row.get(m["abstract"]) or "")[:1500],
        })
    return out, skipped

def existing_keys():
    if not os.path.exists(RAW_PATH): return set()
    with open(RAW_PATH, encoding="utf-8", newline="") as f:
        return {(norm_title(r["title"]), r["sources"], r["query_sets"])
                for r in csv.DictReader(f)}

def append(recs):
    seen, new = existing_keys(), []
    for r in recs:
        k = (norm_title(r["title"]), r["sources"], r["query_sets"])
        if k in seen: continue
        seen.add(k); new.append(r)
    if new:
        exists = os.path.exists(RAW_PATH) and os.path.getsize(RAW_PATH) > 0
        with open(RAW_PATH, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if not exists: w.writerow(RAW)
            for r in new: w.writerow([r[c] for c in RAW])
    return len(new)

def selftest():
    rows = [{"Title": "A Vision-and-Language Navigation Agent", "Year": "2024",
             "Source title": "IEEE RA-L", "Authors": "Doe, J.; Roe, R.; Poe, P.; Moe, M.; Zoe, Z.",
             "DOI": "https://doi.org/10.1/ABC", "Cited by": "12", "Document Type": "Article",
             "Link": "", "Abstract": "We  navigate."},
            {"Title": "Older work", "Year": "2019", "Source title": "X", "Authors": "A, B",
             "DOI": "", "Cited by": "", "Document Type": "", "Link": "", "Abstract": ""}]
    out, skipped = convert(rows, MAPS["scopus"], "scopus", "core")
    assert skipped == 1 and len(out) == 1, (skipped, out)
    r = out[0]
    assert r["doi"] == "10.1/abc" and r["citations"] == 12 and r["n_authors"] == 5
    assert r["authors"].endswith("et al.") and r["url"] == "https://doi.org/10.1/abc"
    assert r["abstract"] == "We navigate."
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    path = args[0]
    def opt(name, default):
        return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
    qset, source = opt("--set", "core"), opt("--source", "scopus")
    if source not in MAPS: sys.exit(f"--source must be one of {', '.join(MAPS)}")
    rows, m = read_export(path, source)
    recs, skipped = convert(rows, m, source, qset)
    print(f"{os.path.basename(path)}: {len(rows)} exported rows, {len(recs)} in window, "
          f"{skipped} outside {YEAR_FROM}+ or untitled")
    if "--dry-run" in sys.argv:
        for r in recs[:5]: print(f"  {r['year']}  {r['title'][:70]}  [{r['venue'][:30]}]")
        print("  (dry run — nothing written)")
    else:
        print(f"appended {append(recs)} new rows to data/corpus_raw.csv "
              f"as source={source}, query_set={qset}")
