#!/usr/bin/env python3
"""Seed recall audit — search_protocol.md §5.7.

Checks how many of the 35 seed works in `data/corpus_seeds.csv` the harvested corpus
actually contains, and which query set found each one. This is the check that
decides whether a query change was worth making: run it after every change and
log the before/after numbers in the protocol.

Seeds published before the 2023 window are out of scope by IC1 and are counted
separately — missing them is correct behaviour, not a recall failure.

  python3 tools/recall_audit.py                  # audit data/corpus_screening.csv
  python3 tools/recall_audit.py data/corpus_raw.csv   # or any harvest output
  python3 tools/recall_audit.py --selftest

Writes data/recall_audit.json.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
WINDOW_FROM = 2023
csv.field_size_limit(10_000_000)

def norm(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())

def keys(row, title_field="title"):
    """Every identifier a record can be matched on."""
    k = set()
    if norm(row.get(title_field)): k.add("t:" + norm(row[title_field]))
    doi = (row.get("doi") or "").lower().replace("https://doi.org/", "").strip()
    if doi: k.add("d:" + doi)
    arx = (row.get("arxiv") or "").split("v")[0].strip()
    if arx: k.add("a:" + arx)
    return k

def audit(corpus_path):
    seeds = list(csv.DictReader(open(os.path.join(DATA, "corpus_seeds.csv"), encoding="utf-8")))
    index = {}
    for row in csv.DictReader(open(corpus_path, encoding="utf-8")):
        for k in keys(row):
            index.setdefault(k, row)

    hits, missed_in, missed_out = [], [], []
    for s in seeds:
        year = int(s["year"]) if (s.get("year") or "").strip().isdigit() else 0
        found = next((index[k] for k in keys(s) if k in index), None)
        entry = {"short": s["short"], "group": s["group"], "year": year,
                 "title": s["title"][:70], "zs_claim": s.get("zs_claim", "")}
        if found:
            entry["found_by"] = found.get("query_sets", "") or "(untagged corpus)"
            entry["sources"] = found.get("sources", "")
            hits.append(entry)
        elif year >= WINDOW_FROM:
            missed_in.append(entry)
        else:
            missed_out.append(entry)

    in_window = [s for s in seeds if (s.get("year") or "0").isdigit() and int(s["year"]) >= WINDOW_FROM]
    per_set = {}
    for h in hits:
        for q in h["found_by"].split("|"):
            per_set[q] = per_set.get(q, 0) + 1

    return {"corpus": os.path.basename(corpus_path), "seeds": len(seeds),
            "found": len(hits), "recall_all": f"{len(hits)}/{len(seeds)}",
            "recall_in_window": f"{len(hits)}/{len(in_window)}",
            "missed_in_window": missed_in, "missed_out_of_window": missed_out,
            "found_by_set": per_set, "hits": hits}

def report(r):
    print(f"\nSeed recall audit — {r['corpus']}")
    print(f"  overall     {r['recall_all']} seed works found")
    print(f"  in window   {r['recall_in_window']} (2023+, the only ones IC1 counts)")
    print(f"  by set      " + ", ".join(f"{k}={v}" for k, v in sorted(r["found_by_set"].items(),
                                                                     key=lambda x: -x[1])))
    if r["missed_in_window"]:
        print(f"\n  MISSED, in window — these are real recall failures:")
        for m in r["missed_in_window"]:
            print(f"    {m['group']}  {m['short']:<18} {m['year']}  {m['title']}")
    else:
        print("\n  No in-window seed is missing.")
    print(f"\n  Missed but pre-{WINDOW_FROM} (correctly out of scope): " +
          (", ".join(m["short"] for m in r["missed_out_of_window"]) or "none"))

def selftest():
    assert norm("Vision-and-Language Navigation!") == norm("vision and language navigation")
    assert keys({"title": "A", "arxiv": "2305.16986v2"}) == {"t:a", "a:2305.16986"}
    assert "d:10.1/x" in keys({"doi": "https://doi.org/10.1/X"})
    assert keys({"title": "", "doi": "", "arxiv": ""}) == set()
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    arg = next((a for a in sys.argv[1:] if not a.startswith("--")), "corpus_screening.csv")
    path = arg if os.path.isabs(arg) or os.path.exists(arg) else os.path.join(DATA, arg)
    r = audit(path)
    report(r)
    json.dump(r, open(os.path.join(DATA, "recall_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nwrote data/recall_audit.json")
