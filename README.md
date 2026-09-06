# Vision-and-Language Navigation — Survey Plan & Corpus

Planning material and the screening corpus for a survey of **Vision-and-Language
Navigation (VLN)** in the era of large foundation models, with a dedicated treatment of
**zero-shot and training-free navigation**. Target format: IEEE two-column.

**Interactive version:** https://gtu-dash-lab.github.io/vln-literature-survey/

Author: Fouad Aladhami — Gebze Technical University

---

## Layout

```
README.md              this file
refresh.sh             one command: rebuild everything and the page
index.html             the built page (generated — edit site/, not this)

docs/                  the plan and the protocol
  survey_outline.md      14-section IEEE outline; Section IX is the zero-shot chapter
  search_protocol.md     RQs, databases, query strings, IC/EC, screening, the recall audits
  seeds_zero_shot.md     35 seed works — the yardstick the queries are graded against
  pipeline.md            how the tools fit together, and the judgement calls inside them

tools/                 the pipeline, in the order it runs
  harvest.py             7 sources x 4 query sets -> the append-only raw log
  merge_export.py        Scopus / WoS exports -> the same log
  screen.py              IC/EC pre-screen -> decision + reason_code
  recall_audit.py        seed recall: does the query actually find the field?
  reading_list.py        the ~100 papers to read, by survey chapter
  build.py               index.html
  make_latex.py          latex/numbers.tex — corpus figures as LaTeX macros
  make_bib.py            latex/refs.bib from doi.org
  fetch_seeds.py         resolves the seed list and its citation counts

data/                  generated; the corpus lives here
  corpus_raw.csv         every hit, one row per record x source — PRISMA identification
  corpus_screening.csv   deduplicated, with the screening columns
  corpus_seeds.{csv,json}  the seed table
  harvest_report.json    per-source, per-set and per-phrase counts
  recall_audit.json      seed recall and what is still missing
  reading_list.{csv,json}  the papers to read

latex/                 the manuscript (upload this directory to Overleaf)
  main.tex               IEEEtran skeleton: 14 sections, 9 figures, 7 tables, PRISMA in TikZ
  numbers.tex            generated — every corpus figure the paper quotes
  refs.bib               generated — the reading list, from the publishers' own records

site/                  page sources
  page.template.html     edit this, never index.html
  fonts.css + *.woff2    six subsetted faces, inlined at build time
```

**Start here:** [`docs/pipeline.md`](docs/pipeline.md) explains how a query string becomes a
reading list, and why each step is shaped the way it is.

## The zero-shot angle

"Zero-shot" is used for at least five different claims in this literature, and papers
routinely compare across them as if they were one. The survey separates them:

| | Claim |
|---|---|
| **ZS-1** | Training-free — no gradient updates for the navigation policy |
| **ZS-2** | Open-vocabulary goal — the goal category was never in a label set |
| **ZS-3** | Cross-dataset — trained on A, evaluated on B |
| **ZS-4** | Unseen environment — the standard R2R val-unseen split |
| **ZS-5** | Cross-embodiment / sim-to-real |

Every zero-shot paper in the corpus is audited against these five, which is what
Table VI in the outline reports.

## Reproducing the corpus

```bash
./refresh.sh              # rebuild corpus, screening, reading list, audit, page and macros
./refresh.sh --harvest    # harvest every source first, then rebuild
```

Or a single step:

```bash
python3 tools/harvest.py                  # all four query sets, all seven sources
python3 tools/harvest.py core             # just one set
python3 tools/harvest.py --only openalex  # one source — how you recover from a rate limit
python3 tools/harvest.py --rebuild        # recompute from the raw log, query nothing
python3 tools/harvest.py --fresh          # discard the raw log and start over
python3 tools/screen.py                   # pre-screen against IC/EC
python3 tools/reading_list.py             # the ~100 papers to read
python3 tools/recall_audit.py             # seed recall against the 35 landmarks
python3 tools/fetch_seeds.py              # refresh the seed table's citation counts
```

`data/corpus_raw.csv` is an **append-only identification log**. Every block of hits is written the
moment it is collected, and each run rebuilds `data/corpus_screening.csv` and `data/harvest_report.json`
from the whole file. A killed run, or one whose source was rate-limiting, therefore costs
nothing: re-run the set, or just the missing source with `--only`.

Rate limits are real here. OpenAlex will 429 a full four-set run and stay closed for hours
afterwards; set `OPENALEX_MAILTO=you@example.org` to use its polite pool, and re-harvest that
one source afterwards. A request that exhausts its retries is recorded as `(incomplete)` in the
report, never as a zero — the distinction is the difference between a real count and a fake one.

Four query sets run, and the split matters:

| Set | What it covers | Why it exists |
|---|---|---|
| `core` | Q1 — the `"…navigation"` phrase family | High precision, the query a Scopus session would run |
| `recall` | Q2/Q4 — `visual language navigation`, `object goal navigation`, `embodied navigation` | Q1 alone recovered **8 of 35** seed works. The field does not agree on what to call the task. |
| `zeroshot` | Q5 — zero-shot / training-free / open-vocabulary navigation | The survey's Section IX; tagged separately because precision is low |
| `enabler` | Open-vocabulary maps, 3D scene graphs, code-as-policy | VLMaps, ConceptGraphs and Code as Policies never say "navigation", and Sections 6.5, 9.3 and 9.6 depend on them |

The seed list in `docs/seeds_zero_shot.md` is the recall check: run the queries, then verify
the result set contains groups A and B. That check is what produced the table above.

Seven sources run. Six need no key at all; IEEE Xplore needs one:

```bash
export IEEE_API_KEY=your-key-here        # developer.ieee.org — free on academic request
python3 tools/harvest.py --only ieee           # adds IEEE records to the existing corpus
```

Keep the key in your shell, never in the repo — this repository is public. The free tier is a
few hundred calls a day, which is why `tools/harvest.py` pages IEEE less deeply than the others.


| Source | What it adds |
|---|---|
| OpenAlex | Phrase search over title and abstract — the closest open analogue to Scopus `TITLE-ABS-KEY` |
| Crossref | The DOI metadata IEEE, ACM, Springer and Elsevier deposit — the keyless stand-in for the publisher databases. Its search is fuzzy, so every hit is re-checked for the phrase |
| IEEE Xplore | CVPR, ICCV, WACV, ICRA, IROS, RA-L, T-RO — the densest venues for this topic. **Needs a key**; skipped silently when `IEEE_API_KEY` is unset |
| Semantic Scholar | Bulk search, and the only source that indexes CV and robotics proceedings references properly |
| arXiv | The preprint stream Scopus cannot see, over cs.CV, cs.RO, cs.AI, cs.CL |
| DBLP | Canonical CS venue resolution; catches published versions the others still hold as preprints |
| OpenReview | NeurIPS, ICLR, ICML and CoRL, on both API hosts. Papers still under review are dropped — anonymous and not peer-reviewed, so IC2 excludes them |

**Scopus and Web of Science need an institutional session** and are not harvested here. Run the
queries from `docs/search_protocol.md` §5 in their web interfaces, export, and merge:

```bash
python3 tools/merge_export.py scopus.csv --set core
python3 tools/merge_export.py savedrecs.txt --set core --source wos
```

The export lands in `data/corpus_raw.csv` tagged `source=scopus`, so it dedupes against the harvested
records on DOI and normalised title and counts in PRISMA like any other source.

## Screening

`tools/screen.py` fills the `decision` and `reason_code` columns of `data/corpus_screening.csv` from
title and abstract keywords, using the protocol's own codes. On the corpus as harvested:

| Decision | Records | What it means |
|---|---:|---|
| `include` | 854 | navigation, language conditioning and visual observation all present |
| `check` | 159 | the gate could not call it — enabler papers, missing abstracts, no stated embodiment |
| `survey` | 61 | EC6, held back for Table I rather than the method corpus |
| `exclude` | 1 544 | EC1–EC5, each row carrying the code that fired |

**This is a pre-screen, not screening.** A keyword gate cannot judge IC4–IC6; what it can do is
group the obvious exclusions so the human pass starts from something ordered, and make the
`check` bucket explicit. Read `check` first. Any decision already written by a human is
preserved — `tools/screen.py` only fills empty cells.

## The reading list

Two thousand records is a corpus; a survey is written from about a hundred papers.
`tools/reading_list.py` picks them from the `include` bucket, 2024 onward, and two decisions
in it need stating in Sec. III because they are arguable:

- **Citations are divided by age.** Raw citation count ranks 2024, not the field — a 2026
  paper has had months to accrue. A paper with 40 citations in 2026 therefore outranks one
  with 90 from 2024.
- **The tier quotas are ceilings, not targets.** A flat top-100 collapses onto the most-cited
  cluster and leaves whole chapters uncited, so the list is filled per chapter. But a tier
  that cannot fill itself from peer-reviewed, cited or seed work is **left short** rather than
  padded with uncited preprints, and the shortfall is reported: *end-to-end VLA policies*
  and *maps / scene graphs* both come up short, which is a finding about the corpus, not a
  bug in the script.

Seed works inside the window are pinned — they are the field's landmarks by construction.

## The manuscript

```bash
python3 tools/make_latex.py     # latex/numbers.tex  (run by refresh.sh)
python3 tools/make_bib.py       # latex/refs.bib     (network; cached in latex/.bibcache)
```

Upload the `latex/` directory to Overleaf and compile `main.tex` — IEEEtran ships with
Overleaf's TeX Live, so nothing else is needed. For IEEE Access, swap the class line for
`\documentclass{ieeeaccess}`.

**No corpus number is typed into the manuscript.** Section III reads
`Identification returned \CorpusRaw{} records`, and the PRISMA figure draws the same macros,
so the prose, the figure and the repository cannot drift apart. Re-run `./refresh.sh` after a
harvest and the manuscript updates with it.

## Building the page

```bash
python3 tools/build.py
```

`index.html` is generated from `site/page.template.html` (structure) plus
`site/fonts.css` (six subsetted woff2 faces, inlined as data URIs) plus
`data/corpus_seeds.json` (data). Edit the template, not the built file.

## Citation counts

Citation counts come from **Semantic Scholar**, not OpenAlex. OpenAlex does not index
the reference lists of most CV and ML proceedings — it reports 61 citations for R2R
against 1,922 on Semantic Scholar, and 21 for HAMT against 409. Ranking this literature
on OpenAlex figures would invert the order. Both numbers are kept per row so the gap
stays visible.
