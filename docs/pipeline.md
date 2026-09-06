# The Pipeline

How a query string becomes a reading list. Nine tools, one raw log, and a rule that runs
through all of it: **every number is generated, never typed.** The page, the manuscript and
this repository read the same files, so they cannot drift apart.

```
        queries (search_protocol.md §5)
                    │
    tools/harvest.py│  7 sources, 4 query sets           ┌─ tools/merge_export.py
                    ▼                                    │  (Scopus / WoS exports)
        data/corpus_raw.csv  ◄───────────────────────────┘
        append-only identification log
                    │
    tools/harvest.py│  --rebuild: dedupe on DOI → arXiv id → normalised title
                    ▼
        data/corpus_screening.csv ──► tools/screen.py  ──► decision + reason_code
                    │
                    ├──► tools/recall_audit.py  ──► data/recall_audit.json
                    ├──► tools/reading_list.py  ──► data/reading_list.{csv,json}
                    ├──► tools/build.py         ──► index.html
                    └──► tools/make_latex.py    ──► latex/numbers.tex
                                                    tools/make_bib.py ──► latex/refs.bib
```

`./refresh.sh` runs everything below the raw log. `./refresh.sh --harvest` runs the harvest
first. Both are safe to repeat.

---

## 1. Harvest — `tools/harvest.py`

Runs four query sets against seven sources and appends every hit to `data/corpus_raw.csv`.

| Set | Phrases | What it is for |
|---|---:|---|
| `core` | 11 | Q1, the `"…navigation"` phrase family. High precision — the query a Scopus session would run |
| `recall` | 16 | The other names the field uses: *visual language navigation*, *object goal navigation*, *embodied navigation*, *visual target navigation*, *lifelong navigation* |
| `zeroshot` | 8 | Zero-shot, training-free, open-vocabulary. Tagged separately because it feeds Section IX and its precision is low |
| `enabler` | 9 | Open-vocabulary maps, 3D scene graphs, code-as-policy. These papers never say *navigation* |

| Source | Key | What only it contributes |
|---|---|---|
| OpenAlex | no | Phrase search over title and abstract — the closest open analogue to Scopus `TITLE-ABS-KEY` |
| Crossref | no | The DOI metadata IEEE, ACM, Springer and Elsevier deposit |
| Semantic Scholar | no | Proper reference lists for CV and robotics proceedings |
| arXiv | no | The preprint stream Scopus cannot see |
| DBLP | no | Canonical CS venue names; catches published versions of things others hold as preprints |
| OpenReview | no | NeurIPS, ICLR, ICML, CoRL — the venues neither Scopus nor WoS index |
| IEEE Xplore | `IEEE_API_KEY` | CVPR, ICCV, WACV, ICRA, IROS, RA-L, T-RO |

Scopus and Web of Science need an institutional session; export them and use
`tools/merge_export.py`, which writes into the same raw log tagged `source=scopus`.

### Three properties worth knowing

**The raw log is append-only.** Each block of hits is written the moment it is collected, and
any run rebuilds the corpus and the report from the whole file. A killed run costs nothing:
re-run the set, or one source with `--only`, and the rows are added to what is there.

**A throttled request is not a zero.** OpenAlex will rate-limit a full four-set run and stay
closed for hours; OpenReview does the same on a shorter cycle. When a request exhausts its
retries the phrase is recorded as `(incomplete)`, never as a count of zero, and the page says
so. A phrase throttled into silence must not enter the PRISMA figures as a phrase that found
nothing.

**Set `OPENALEX_MAILTO`** to join OpenAlex's polite pool. With it, a full four-set OpenAlex
pass takes about six minutes; without it, it will lock you out.

```bash
export OPENALEX_MAILTO=you@example.org
export IEEE_API_KEY=...            # optional; the source is skipped without it
python3 tools/harvest.py           # everything
python3 tools/harvest.py --only openalex    # one source, e.g. after a rate limit
python3 tools/harvest.py --rebuild          # recompute from the log, query nothing
python3 tools/harvest.py --fresh            # discard the log and start over
```

## 2. Pre-screen — `tools/screen.py`

Fills `decision` and `reason_code` from title and abstract keywords, using the protocol's own
codes: `include`, `check`, `survey` (EC6), or `exclude` with EC1–EC7.

**It is a pre-screen, not screening.** A keyword gate cannot judge IC4–IC6. What it can do is
group the obvious exclusions so the human pass starts from something ordered, and make the
`check` bucket explicit — read that one first. Decisions a human has already written are never
overwritten; the script only fills empty cells.

Three gates exist because the list surfaced them as false positives, and each has a self-test:

- **GUI and web agents** "navigate" a screen, not a 3D environment.
- **Autonomous driving** is a different problem and a different community (EC5) — a navigation
  phrase in the title does not make an autonomous-vehicle dataset embodied navigation.
- **Navigation mentioned in passing** — a manipulation paper that says "navigating the
  workspace" matches the vocabulary without being navigation work, so the word has to appear in
  the title or twice in the abstract.

## 3. Recall audit — `tools/recall_audit.py`

The 35 seed works in `docs/seeds_zero_shot.md` are the measuring stick: run the queries, then
check how many come back. This is what decides whether a query set earns its place, and
§5.7 of the protocol requires re-running it after every query change.

The loop it drove: **8/26 → 23/26 → 26/26** in-window recall. The single-phrase core set alone
still reaches only 8 — that number is the answer to "why not just run Q1 in Scopus".

## 4. Reading list — `tools/reading_list.py`

Picks the ~100 papers to actually read, from the `include` bucket, 2024 onward. Two judgements
are baked in and both belong in Sec. III of the manuscript:

**Citations are divided by age.** Raw counts rank 2024, not the field; a 2026 paper has had
months to accrue. A 2026 paper with 40 citations therefore outranks a 2024 paper with 90.

**Tier quotas are ceilings, not targets.** A flat top-100 collapses onto the most-cited cluster
and leaves whole chapters uncited, so the list fills per chapter — but a tier that cannot fill
itself from peer-reviewed, cited or seed work is left short rather than padded. Two tiers come
up short, and that shortfall is a finding about the corpus, not a bug.

## 5. Outputs

| Tool | Writes | Consumed by |
|---|---|---|
| `tools/build.py` | `index.html` | the published page; every figure injected from the data files |
| `tools/make_latex.py` | `latex/numbers.tex` | `latex/main.tex` — Sec. III prose and the PRISMA figure draw the same macros |
| `tools/make_bib.py` | `latex/refs.bib` | the manuscript; entries come from doi.org, so they are the publisher's own record |
| `tools/fetch_seeds.py` | `data/corpus_seeds.{csv,json}` | the seed table and the recall audit |

## 6. Adding a source

1. Write a function in `tools/harvest.py` returning the record shape `blank()` defines.
2. Add its name to `SOURCES` and a `want("name")` block in the per-set loop.
3. Every hit must be re-checked for the phrase if the API's search is fuzzy — Crossref and
   IEEE both are.
4. Run `python3 tools/harvest.py --only <name>`, then `./refresh.sh`.
5. Re-run the recall audit and log the before/after in `docs/search_protocol.md` §5.8.

Nothing already on file is fetched twice, so a new source costs only its own API time.
