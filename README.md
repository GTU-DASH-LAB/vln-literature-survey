# Vision-and-Language Navigation — Survey Plan & Corpus

Planning material and the screening corpus for a survey of **Vision-and-Language
Navigation (VLN)** in the era of large foundation models, with a dedicated treatment of
**zero-shot and training-free navigation**. Target format: IEEE two-column.

**Interactive version:** https://gtu-dash-lab.github.io/vln-literature-survey/

Author: Fouad Aladhami — Gebze Technical University

---

## What is here

| File | What it is |
|---|---|
| [`survey_outline.md`](survey_outline.md) | The section-by-section outline (14 sections). Section IX is the zero-shot chapter. Includes the organising-axis decision and the figure/table plan. |
| [`search_protocol.md`](search_protocol.md) | The review protocol: research questions, time window, database tiers, the five executable queries, inclusion/exclusion criteria with reason codes, the screening pipeline, and the data-extraction sheet. |
| [`seeds_zero_shot.md`](seeds_zero_shot.md) | 35 seed works grouped A–F, with resolved venues and citation counts. Used as a recall check on every query and as the snowballing entry point. |
| [`index.html`](index.html) | Self-contained interactive page — the outline, the queries with copy buttons, and the seed table with sorting and filtering. No external requests. |
| `corpus_seeds.{csv,json}` | The seed table, machine-readable. |
| `corpus_raw.csv` | Every hit, one row per record × source, tagged with the query set and phrase that found it. These are the PRISMA *identification* counts. |
| `corpus_screening.csv` | The deduplicated corpus with empty `decision` / `reason_code` columns — the sheet screening is actually done in. |
| `harvest_report.json` | Per-set, per-source and per-phrase hit counts for the PRISMA flow diagram. |
| `fetch_seeds.py` | Resolves the seed list against OpenAlex, then re-counts citations through the Semantic Scholar batch endpoint. |
| `harvest.py` | Runs the four query sets against OpenAlex, Semantic Scholar and arXiv; deduplicates and writes the corpus files. |

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
python3 harvest.py          # all four query sets -> corpus_raw.csv, corpus_screening.csv, harvest_report.json
python3 harvest.py core     # just one set
python3 fetch_seeds.py      # refreshes the seed table's citation counts
```

Four query sets run, and the split matters:

| Set | What it covers | Why it exists |
|---|---|---|
| `core` | Q1 — the `"…navigation"` phrase family | High precision, the query a Scopus session would run |
| `recall` | Q2/Q4 — `visual language navigation`, `object goal navigation`, `embodied navigation` | Q1 alone recovered **8 of 35** seed works. The field does not agree on what to call the task. |
| `zeroshot` | Q5 — zero-shot / training-free / open-vocabulary navigation | The survey's Section IX; tagged separately because precision is low |
| `enabler` | Open-vocabulary maps, 3D scene graphs, code-as-policy | VLMaps, ConceptGraphs and Code as Policies never say "navigation", and Sections 6.5, 9.3 and 9.6 depend on them |

The seed list in `seeds_zero_shot.md` is the recall check: run the queries, then verify
the result set contains groups A and B. That check is what produced the table above.

Both use only public APIs (OpenAlex, Semantic Scholar, arXiv) and need no keys.

**Scopus and Web of Science are not harvested here** — they need an institutional
session. Run Q1 and Q2 from `search_protocol.md` §5 in their web interfaces, export
CSV, and merge on DOI / normalised title. The harvest output is shaped so that merge
is a straight append.

## Building the page

```bash
python3 build.py
```

`index.html` is generated from `build/page.template.html` (structure) plus
`build/fonts.css` (six subsetted woff2 faces, inlined as data URIs) plus
`corpus_seeds.json` (data). Edit the template, not the built file.

## Citation counts

Citation counts come from **Semantic Scholar**, not OpenAlex. OpenAlex does not index
the reference lists of most CV and ML proceedings — it reports 61 citations for R2R
against 1,922 on Semantic Scholar, and 21 for HAMT against 409. Ranking this literature
on OpenAlex figures would invert the order. Both numbers are kept per row so the gap
stays visible.
