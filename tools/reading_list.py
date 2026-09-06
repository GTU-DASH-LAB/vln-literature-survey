#!/usr/bin/env python3
"""Pick the ~100 papers to actually read, from the pre-screened corpus.

The corpus is 2 600 records; a survey is written from roughly a hundred. This picks them.

Two judgements are baked in, and both belong in Sec. III:

1. **Citations are age-normalised.** Raw citation count is a ranking of 2024, not of the
   field: a 2026 paper has had months to accrue. Ranking uses citations per year since
   publication, so a 2026 paper with 40 citations outranks a 2024 paper with 90.
2. **Section quotas, not a single ranking.** A flat top-100 collapses onto whatever the
   most-cited cluster is and leaves whole sections of the outline uncited. The quotas below
   force the list to span the survey, so every chapter has something to be written from.

Seed works inside the window are pinned: they are the field's landmarks by construction.

  python3 tools/reading_list.py            # -> data/reading_list.csv, data/reading_list.json
  python3 tools/reading_list.py --n 150    # a longer list, quotas scale with it
  python3 tools/reading_list.py --selftest
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
csv.field_size_limit(10_000_000)
NOW = 2026
FROM = 2024

# tier -> (share of the list, matcher, why it is a tier of its own)
TIERS = [
 ("T1 zero-shot / training-free", .30,
  re.compile(r"zero-?shot|training-?free|open-vocabulary|open vocabulary|open-set|"
             r"without fine-?tuning|off-the-shelf|in-context", re.I),
  "Section IX is the survey's argument. Read all of these."),
 ("T2 instruction-following VLN", .25,
  re.compile(r"vision-and-language navigation|\bvln\b|instruction[- ]following|"
             r"room-to-room|\br2r\b|\brxr\b|reverie|language-guided navigation|"
             r"instruction navigation", re.I),
  "The supervised line the zero-shot work is measured against — Sections VII–VIII."),
 ("T3 end-to-end VLA / video policies", .15,
  re.compile(r"vision-language-action|\bvla\b|video-language|end-to-end polic|"
             r"navigation polic|foundation model.{0,30}navigat|generalist", re.I),
  "The competing paradigm: one model, no pipeline. Sections VIII and XII."),
 ("T4 benchmarks, datasets, simulators", .12,
  re.compile(r"\bbenchmark\b|\bdataset\b|\bsimulator\b|\bsuite\b|\btestbed\b|"
             r"habitat|matterport|ai2-?thor|procthor|\bhm3d\b|goat-bench", re.I),
  "Section V and Tables II–V. Without these the comparison tables cannot be built."),
 ("T5 real robot / sim-to-real", .10,
  re.compile(r"real[- ]world|real robot|sim-?to-?real|deploy\w*|physical robot|"
             r"quadruped|\bwheelchair\b|onboard|hardware", re.I),
  "RQ4. The gap between a leaderboard and a robot is a chapter of its own — Section X."),
 ("T6 maps, scene graphs, enablers", .08,
  re.compile(r"scene graph|semantic map|open-vocabulary map|visual language map|"
             r"queryable|3d map|scene representation|code as policies", re.I),
  "Sections 6.5 and 9.3. These never say 'navigation' but the methods stand on them."),
]

def n_int(v):
    v = str(v or "").strip()
    return int(v) if v.lstrip("-").isdigit() else 0

def peer_reviewed(r):
    v = (r.get("venue") or "").strip().lower()
    return bool(v) and not re.match(r"^(arxiv|corr)\b", v)

def per_year(r):
    """Citations per year since publication — the ranking signal."""
    y = n_int(r.get("year")) or NOW
    return n_int(r.get("citations")) / max(1, NOW - y + 1)

def score(r, is_seed):
    s = per_year(r)
    if peer_reviewed(r): s *= 1.25          # a venue is evidence a peer read it
    s += 2 * len([x for x in (r.get("sources") or "").split("|") if x])   # source agreement
    if is_seed: s += 1000                   # landmarks are pinned, not ranked
    return s

def tier_of(r):
    text = f"{r.get('title','')} {r.get('abstract','')}"
    for name, _, rx, _ in TIERS:
        if rx.search(text):
            return name
    return ""

def norm(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())

def build(n=100):
    rows = list(csv.DictReader(open(os.path.join(DATA, "corpus_screening.csv"), encoding="utf-8")))
    seeds = {norm(s["title"]) for s in
             csv.DictReader(open(os.path.join(DATA, "corpus_seeds.csv"), encoding="utf-8"))}

    pool = [r for r in rows
            if r.get("decision") == "include"
            and FROM <= n_int(r.get("year")) <= NOW]
    for r in pool:
        r["is_seed"] = norm(r["title"]) in seeds
        r["tier"] = tier_of(r)
        r["score"] = score(r, r["is_seed"])
        r["cites_per_year"] = round(per_year(r), 1)
    pool.sort(key=lambda r: -r["score"])

    # A quota is a ceiling, not a target. Filling T5 with 2026 preprints nobody has read
    # yet would hide the actual finding, which is that this corpus is thin on real-robot work.
    def worth_reading(r):
        return r["is_seed"] or peer_reviewed(r) or n_int(r.get("citations")) >= 3

    picked, seen, short = [], set(), {}
    for name, share, _, _ in TIERS:
        quota = max(1, round(n * share))
        for r in pool:
            if len([p for p in picked if p["tier"] == name]) >= quota: break
            if r["tier"] != name or norm(r["title"]) in seen: continue
            if not worth_reading(r): continue
            seen.add(norm(r["title"])); picked.append(r)
        got = len([p for p in picked if p["tier"] == name])
        if got < quota: short[name] = (got, quota)
    # any seed work still unpicked is pinned in regardless of its tier's quota
    for r in pool:
        if r["is_seed"] and norm(r["title"]) not in seen:
            seen.add(norm(r["title"])); r["tier"] = r["tier"] or "T2 instruction-following VLN"
            picked.append(r)

    order = {t[0]: i for i, t in enumerate(TIERS)}
    picked.sort(key=lambda r: (order.get(r["tier"], 9), -r["score"]))
    for i, r in enumerate(picked, 1):
        r["rank"] = i
    return picked, len(pool), short

COLS = ["rank", "tier", "is_seed", "title", "year", "venue", "citations", "cites_per_year",
        "task", "zs_claim", "doi", "arxiv", "url", "query_sets", "sources", "abstract"]

def selftest():
    old = {"year": "2024", "citations": "90", "venue": "IEEE RA-L"}
    new = {"year": "2026", "citations": "40", "venue": "IEEE RA-L"}
    assert per_year(new) > per_year(old), "age normalisation must favour the recent paper"
    assert peer_reviewed({"venue": "CoRL"}) and not peer_reviewed({"venue": "arXiv (preprint)"})
    assert tier_of({"title": "Zero-shot object navigation", "abstract": ""}).startswith("T1")
    assert tier_of({"title": "A new R2R agent", "abstract": "vision-and-language navigation"}).startswith("T2")
    assert n_int("") == 0 and n_int("12") == 12
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 100
    picked, pool, short = build(n)

    with open(os.path.join(DATA, "reading_list.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for r in picked: w.writerow(r)
    json.dump({"tiers": [{"name": t[0], "note": t[3]} for t in TIERS],
               "pool": pool, "from_year": FROM, "to_year": NOW,
               "short": {k: {"got": v[0], "quota": v[1]} for k, v in short.items()},
               "rows": [{k: r.get(k) for k in COLS if k != "abstract"} |
                        {"abstract": (r.get("abstract") or "")[:420]} for r in picked]},
              open(os.path.join(DATA, "reading_list.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"{len(picked)} papers picked from a pool of {pool} "
          f"({FROM}-{NOW}, pre-screened include)\n")
    for name, share, _, _ in TIERS:
        g = [r for r in picked if r["tier"] == name]
        if not g: continue
        pr = sum(1 for r in g if peer_reviewed(r))
        sd = sum(1 for r in g if r["is_seed"])
        print(f"  {name:<34} {len(g):>3}  (peer-reviewed {pr}, seed works {sd}, "
              f"median cites/yr {sorted(r['cites_per_year'] for r in g)[len(g)//2]})")
    for name, (got, quota) in short.items():
        print(f"\n  ! {name}: {got} of {quota} slots filled. Nothing else in the corpus is "
              f"peer-reviewed, cited or a seed work — that thinness is itself a finding.")
    print("\n-> data/reading_list.csv, data/reading_list.json")
