# Review Protocol — Databases, Keywords, Screening
Feeds Section III of `survey_outline.md`. Freeze this **before** collecting papers; log every
deviation with a date.

---

## 1. Research questions (draft)

- **RQ1** How are large language and vision-language models integrated into camera-based
  navigation agents, and what architectural roles do they take (planner, policy, teacher, critic)?
- **RQ2** What visual observation and scene-representation choices dominate post-2023 VLN, and
  how do they affect performance?
- **RQ3** Which datasets, simulators and benchmarks are used, and how comparable are the
  reported results?
- **RQ4** How far has VLN progressed from simulation to real robot deployment, and what limits it?
- **RQ5** To what extent can navigation be performed **zero-shot / training-free**, which senses
  of "zero-shot" are actually being claimed, and how large is the remaining gap to supervised
  state of the art in accuracy, cost and latency?
- **RQ6** What are the open challenges and the most promising research directions?

## 2. Time window

**2023-01-01 → 2026-09-30**, justified in-text by the post-ChatGPT/GPT-4 shift to
foundation-model agents. Pre-2023 work (R2R 2018, VLN-BERT, HAMT, DUET, VLN-CE …) is cited as
**background** in Sec. II and 8.1 but is *excluded from the systematic corpus and from all
PRISMA counts* — say this explicitly, it is a common reviewer complaint.

---

## 3. Database selection and rationale

### Tier 1 — primary systematic sources (run the full protocol, export BibTeX/CSV, count in PRISMA)

| Database | Why | Caveat |
|---|---|---|
| **Scopus** | Broadest single index for this field: covers IEEE, ACM, Springer (ECCV), Elsevier; best advanced-search syntax and export | Misses NeurIPS/ICLR/ICML/CoRL (PMLR & OpenReview are not indexed) |
| **Web of Science Core Collection** | CPCI-S indexes CVPR/ICCV/ICRA/IROS; required if you want citation-based bibliometrics (VOSviewer) | Narrower than Scopus; check your GTU subscription covers CPCI-S |
| **IEEE Xplore** | Full text of CVPR/ICCV/WACV, ICRA, IROS, RA-L, T-RO, IEEE Access — the densest venues for this topic | Overlaps Scopus heavily; keep it for full-text search and PDF access |

### Tier 2 — mandatory complement for a 2023–2026 LLM topic

| Source | Why |
|---|---|
| **arXiv (cs.CV, cs.RO, cs.AI, cs.CL)** | The majority of 2025–2026 VLN work appears here first. Excluding it makes the survey stale on arrival. Use the arXiv API, not the web UI |
| **OpenReview + PMLR** | NeurIPS / ICLR / ICML / **CoRL** — the venues Scopus and WoS do not index, and CoRL is central to embodied navigation |
| **DBLP / Semantic Scholar API** | Deduplication, canonical venue resolution, and forward-citation snowballing at scale |

### Tier 3 — supporting, not counted as primary

- **ACM Digital Library** — some HRI, ACM MM, UIST/AR wayfinding work. Run the query, keep only unique hits.
- **Google Scholar** — **use only for snowballing and for finding the peer-reviewed version of an
  arXiv entry.** Its boolean support is shallow (≈256 chars, no field operators worth trusting) and
  results are not reproducibly exportable, so it must not be a PRISMA identification source.
  If you insist on counting it, export via Publish or Perish and say so.
- **ScienceDirect** — a strict subset of Scopus. Running it separately only inflates duplicates.
  Skip it unless you specifically want full text from *Robotics and Autonomous Systems*,
  *Neurocomputing*, *Pattern Recognition*, *Expert Systems with Applications*.
- **PubMed** — **drop it.** No robotics VLN coverage. The single exception is if you keep the
  assistive-navigation-for-blind-users application thread (Sec. XI); then run one narrow query
  there and say it returned N hits, M included.

**Bottom line:** Scopus + WoS + IEEE Xplore + arXiv + OpenReview/PMLR is the defensible set.
Five sources, no redundancy, full coverage of the field's actual publication venues.

---

## 4. Concept blocks (build every query from these)

- **A — Task/action:** navigation, navigate, wayfinding, path planning, route following,
  exploration, goal-reaching
- **B — Language:** natural language, instruction, language-guided, language-driven,
  language-conditioned, referring expression, dialogue, text-guided
- **C — Vision/embodiment:** visual, vision, camera, RGB, RGB-D, egocentric, monocular,
  panoramic, embodied, mobile robot, UAV, quadruped
- **D — Foundation models:** large language model, LLM, vision-language model, VLM,
  multimodal large language model, MLLM, foundation model, GPT-4, vision-language-action, VLA
- **F — Zero-shot / generalisation:** zero-shot, zero shot, training-free, training free,
  open-vocabulary, open vocabulary, open-set, open-world, off-the-shelf, without fine-tuning,
  in-context learning, prompt-based, few-shot, unseen category, unseen environment,
  cross-dataset generalization, generalizable, generalist
- **E — Named benchmarks/simulators (high-precision recall booster):** Room-to-Room, R2R, RxR,
  REVERIE, SOON, CVDN, Touchdown, VLN-CE, ObjectNav, ALFRED, Matterport3D, HM3D, Habitat,
  AI2-THOR, ProcTHOR, GOAT-Bench, Isaac Sim

Note on the acronym **VLN**: never search it bare — it collides with unrelated terms.
Always pair it with a navigation/robotics term or restrict it to the keyword field.

---

## 5. Query strings

### 5.1 Scopus — Advanced search (`Search > Advanced document search`)

**Q1 — core, high precision**
```
TITLE-ABS-KEY ( "vision-and-language navigation"  OR  "vision language navigation"
    OR  "vision-language navigation"  OR  "language-guided navigation"
    OR  "language guided navigation"  OR  "language-driven navigation"
    OR  "language-conditioned navigation"  OR  "instruction-following navigation"
    OR  "instruction following navigation"  OR  "natural language navigation"
    OR  "text-guided navigation"  OR  "语言导航" )
AND  PUBYEAR  >  2022
AND  ( LIMIT-TO ( LANGUAGE , "English" ) )
```
*(drop the Chinese phrase unless you want CNKI-indexed items; it is there only as a reminder that
non-English duplicates exist)*

**Q2 — recall, faceted (A AND B AND C)**
```
TITLE-ABS-KEY ( ( navigat*  OR  wayfinding  OR  "path planning"  OR  "route following" )
  AND ( "natural language"  OR  instruction*  OR  "referring expression"  OR  dialog*
        OR  "language-guided"  OR  "language-driven"  OR  "language-conditioned" )
  AND ( visual  OR  vision  OR  camera  OR  RGB*  OR  egocentric  OR  monocular
        OR  panoram*  OR  embodied ) )
AND  PUBYEAR  >  2022
AND ( LIMIT-TO ( SUBJAREA , "COMP" ) OR LIMIT-TO ( SUBJAREA , "ENGI" ) )
AND ( LIMIT-TO ( DOCTYPE , "cp" ) OR LIMIT-TO ( DOCTYPE , "ar" ) OR LIMIT-TO ( DOCTYPE , "re" ) )
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

**Q3 — foundation-model axis (D AND A AND C)**
```
TITLE-ABS-KEY ( ( "large language model*"  OR  LLM  OR  "foundation model*"
        OR  "vision-language model*"  OR  "vision language model*"  OR  VLM
        OR  "multimodal large language model*"  OR  MLLM  OR  "GPT-4*"
        OR  "vision-language-action"  OR  "vision language action" )
  AND ( navigat*  OR  wayfinding  OR  "path planning" )
  AND ( robot*  OR  embodied  OR  "mobile agent*"  OR  UAV  OR  drone  OR  quadruped ) )
AND  PUBYEAR  >  2022
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

**Q4 — benchmark-name recall booster (E AND A)**
```
TITLE-ABS-KEY ( ( "Room-to-Room"  OR  "R2R"  OR  "RxR"  OR  "Room-Across-Room"  OR  REVERIE
        OR  CVDN  OR  Touchdown  OR  "VLN-CE"  OR  "Matterport3D"  OR  "HM3D"  OR  Habitat
        OR  "AI2-THOR"  OR  ProcTHOR  OR  ObjectNav  OR  "object goal navigation"
        OR  ALFRED  OR  "GOAT-Bench" )
  AND ( navigat*  OR  embodied  OR  instruction* ) )
AND  PUBYEAR  >  2022
```
**Q5 — zero-shot / training-free axis (F AND A AND C) — run this one separately and keep its
result set tagged, it feeds Sec. IX and Tables VI–VII**
```
TITLE-ABS-KEY ( ( "zero-shot"  OR  "zero shot"  OR  "training-free"  OR  "training free"
        OR  "open-vocabulary"  OR  "open vocabulary"  OR  "open-set"  OR  "open-world"
        OR  "off-the-shelf"  OR  "without fine-tuning"  OR  "in-context learning" )
  AND ( navigat*  OR  wayfinding  OR  "object goal navigation"  OR  ObjectNav  OR  exploration )
  AND ( robot*  OR  embodied  OR  agent* )
  AND ( visual  OR  vision  OR  camera  OR  RGB*  OR  semantic  OR  "language" ) )
AND  PUBYEAR  >  2022
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```
Precision warning: `"zero-shot"` is one of the most over-used strings in ML abstracts. Expect a
low precision rate on Q5 and screen it manually; the `AND (navigat* OR ... ObjectNav ...)` block is
what keeps it tractable. Do **not** relax the navigation block to boost recall.

Final Scopus set = Q1 ∪ Q2 ∪ Q3 ∪ Q4 ∪ Q5, deduplicated. Export **CSV with abstracts + references**
(needed for VOSviewer co-citation) *and* BibTeX.

### 5.2 Web of Science Core Collection — Advanced search

```
TS=("vision-and-language navigation" OR "vision language navigation" OR "language-guided navigation"
    OR "language-driven navigation" OR "instruction-following navigation"
    OR "natural language navigation" OR "language-conditioned navigation")
```
then
```
TS=(("large language model*" OR LLM OR "vision-language model*" OR "foundation model*" OR MLLM)
    AND (navigat* OR wayfinding) AND (robot* OR embodied OR visual OR camera))
```
then
```
TS=(("zero-shot" OR "training-free" OR "open-vocabulary" OR "open-set" OR "off-the-shelf")
    AND (navigat* OR ObjectNav OR "object goal navigation")
    AND (robot* OR embodied) AND (visual OR vision OR camera OR language))
```
Refine with: Publication Years 2023–2026 · Document Types = Article, Proceedings Paper, Review ·
WoS Categories = *Computer Science, Artificial Intelligence* / *Robotics* /
*Computer Science, Information Systems* / *Engineering, Electrical & Electronic* ·
Language = English. Export as **Tab-delimited / Plain text, "Full Record and Cited References"**.

### 5.3 IEEE Xplore — Command Search
Xplore chokes on very long boolean strings — split into 2–3 queries of ≤10 terms each.

```
("All Metadata":"vision-and-language navigation") OR ("All Metadata":"vision language navigation")
OR ("All Metadata":"language-guided navigation") OR ("All Metadata":"language-driven navigation")
OR ("All Metadata":"instruction following navigation")
```
```
("Abstract":"large language model" OR "Abstract":"vision-language model" OR "Abstract":"foundation model")
AND ("Abstract":navigation) AND ("Abstract":robot OR "Abstract":embodied)
```
```
("Abstract":"zero-shot" OR "Abstract":"training-free" OR "Abstract":"open-vocabulary")
AND ("Abstract":navigation) AND ("Abstract":robot OR "Abstract":embodied)
```
Filters: Year 2023–2026 · Content type = Conferences + Journals & Magazines + Early Access.

### 5.4 ACM Digital Library
```
Title OR Abstract: "vision-and-language navigation" OR "language-guided navigation"
  OR ("large language model" AND navigation AND robot)
```
Filter: 2023–2026, Research Article + Short Paper.

### 5.5 arXiv — via the API, not the web form
Categories `cs.CV`, `cs.RO`, `cs.AI`, `cs.CL`; date range 2023-01-01 → today.
```
(all:"vision-and-language navigation" OR all:"vision language navigation"
 OR all:"language-guided navigation" OR all:"instruction following navigation"
 OR (all:"large language model" AND all:navigation AND all:robot)
 OR ((all:"zero-shot" OR all:"training-free" OR all:"open-vocabulary")
     AND all:navigation AND (all:robot OR all:embodied)))
AND (cat:cs.CV OR cat:cs.RO OR cat:cs.AI OR cat:cs.CL)
```
Then, for every arXiv hit, resolve the peer-reviewed version through DBLP / Semantic Scholar and
keep only one record per work (prefer the published version; keep the arXiv one only if unpublished).

### 5.6 OpenReview / PMLR
Manually sweep NeurIPS, ICLR, ICML **2023–2026** and **CoRL 2023–2025** proceedings pages for
title/abstract matches on blocks A+B and A+D. Log counts like any other source.

### 5.7 Recall audit — executed 2026-09-05, and what it changed

The audit is the one in `seeds_zero_shot.md`: run the query, then check how many of the
35 seed works come back. **Q1 alone returned 8 of 35.** Nine of the misses are pre-2023
and correctly out of window. The other **18 are in window and were genuinely missed**,
for three distinct reasons:

| Why it was missed | Seeds lost | Fix |
|---|---|---|
| The field calls the task something else — `object goal navigation`, `embodied navigation`, `instruction navigation` | CoW, ESC, L3MVN, VLFM, SG-Nav, VoroNav, OpenFMNav, InstructNav, Uni-NaVid | Query set `recall` |
| Q1 lists `vision language navigation` but **not** `visual language navigation` — a spelling a large minority of the field uses | DiscussNav | Added to `recall` |
| The paper is an enabler that never uses the word *navigation* at all — it is about maps, scene graphs or code generation | VLMaps, NLMap, ConceptFusion, ConceptGraphs, HOV-SG, Code as Policies | Query set `enabler` |

Consequences for the protocol:

1. **Q1 is not sufficient on its own**, and neither is a Scopus session that runs only
   Q1. It is a precision query, and the zero-shot half of the survey (Section IX) is
   exactly where its recall collapses — the papers that most need to be found are the
   ones that avoid the phrase.
2. **Run Q2, Q4 and Q5 in Scopus as well**, not just Q1. Report the union in PRISMA, and
   report per-query counts so the identification numbers stay auditable.
3. The `enabler` set is tagged separately and is **not** a VLN query. Its hits feed
   Sections 6.5, 9.3 and 9.6 only. Screen it against IC/EC like any other source, but do
   not let it inflate the headline "VLN papers found" figure.
4. Re-run this audit after any query change, and log the before/after seed recall.

`harvest.py` implements all four sets and tags every record with the set and phrase that
found it, so any of these numbers can be recomputed from `corpus_raw.csv`.

---

## 6. Inclusion / exclusion criteria

**Include (IC)**
- IC1 Published 2023-01-01 – 2026-09-30
- IC2 Peer-reviewed paper, or an arXiv preprint satisfying the preprint rule (below)
- IC3 Written in English, full text obtainable
- IC4 The agent navigates in a 3D environment (sim or real) using **visual observations**
- IC5 Navigation behaviour is conditioned on **natural language** (instruction, goal description,
      dialogue, or open-vocabulary object name)
- IC6 The paper contributes a method, dataset/benchmark, system, or empirical study

**Exclude (EC)**
- EC1 Language-free navigation (pure geometric SLAM/exploration, PointNav without language)
- EC2 Vision-free "navigation" (text-only maze/graph agents, pure LLM planning with no visual input)
- EC3 Manipulation-only or tabletop VLA work with no navigation component
- EC4 Non-embodied vision-language work (VQA, captioning, retrieval) with no navigation task
- EC5 Autonomous driving / lane-level navigation (different problem, different community) —
      *decide once and state it; a "language-guided driving" carve-out is defensible but must be explicit*
- EC6 Surveys and review papers (collected separately for Table I, not part of the method corpus)
- EC7 Workshop abstracts < 4 pages, posters, tech reports without evaluation
- EC8 Duplicate / extended-version pairs (keep the most complete version)

**Zero-shot boundary note (decide once, state it in Sec. III):** zero-shot **ObjectNav** papers
are *included* — an open-vocabulary object category is natural-language conditioning under IC5,
and excluding them would gut Sec. IX. But keep them tagged as `task=ObjectNav` so Table VII never
mixes ObjectNav SR with R2R SR. Pure **PointNav** and image-goal navigation stay excluded (EC1)
unless language is part of the goal specification.

**Preprint rule (write this verbatim into Sec. III, reviewers will ask):**
an arXiv-only paper is included if it meets IC4–IC6 **and** at least one of:
(a) ≥ 10 citations per Semantic Scholar, (b) it introduces a benchmark/dataset already used by
other included papers, or (c) it reports state-of-the-art on a standard benchmark. Mark every
such entry as "preprint" in Table III.

---

## 7. Screening pipeline (record the number at every arrow → this is the PRISMA figure)

```
Identification    per-database raw hits            N1 (report per source)
      ↓ deduplication (Zotero "Duplicate Items" + DOI/title normalisation)
Screening         title + abstract screening        N2 → excluded with reason code (EC1…EC8)
      ↓
Eligibility       full-text assessment              N3 → excluded with reason code
      ↓
Snowballing       backward (reference lists of included papers)
                  forward (Semantic Scholar / Google Scholar "cited by")   +N4
      ↓
Included          final corpus                      N5
```

Tooling: **Zotero** (+ Better BibTeX → `.bib` for IEEEtran, pin citation keys) for the library;
**Rayyan** or **ASReview** for two-pass screening with reason codes; **VOSviewer** or the R
package **bibliometrix** for Figs. 3–5 from the Scopus/WoS exports.

Single-author screening is a validity threat — mitigate it by re-screening a random 10 % sample
after a one-week gap and reporting the intra-rater agreement (Cohen's κ). Put this in Sec. 3.8.

---

## 8. Data extraction sheet (one row per included paper → becomes Table III)

`key · year · venue · type(method|dataset|system|study) · task(R2R/RxR/REVERIE/ObjectNav/…) ·
sim_or_real · embodiment · observation(mono|pano|RGB-D|multi) · scene_repr(none|metric|semantic|
topo|BEV|3DSG|openvocab_map) · language_module · LLM/VLM used (name, size, open/closed) ·
LLM_role(planner|policy|teacher|critic|none) · action_space(discrete|waypoint|velocity) ·
supervision(supervised|pretrain-finetune|few-shot|zero-shot) · benchmark · SR · SPL · nDTW ·
real-robot eval(y/n) · code(y/n) · limitation`

**Zero-shot sub-sheet** (extra columns, filled only for papers tagged `zero-shot`; this becomes
Tables VI–VII):

`zs_claim(ZS-1…ZS-5, may be multiple) · zs_claimed_vs_actual(note) · training_free(y/n) ·
what_was_pretrained(CLIP|BLIP|detector|waypoint predictor|none) · in_domain_data_touched(y/n/partial) ·
backbone(name+version) · backbone_open_weights(y/n) · prompt_strategy(CoT|ReAct|discussion|
map-guided|code) · exploration(frontier|graph|learned|oracle) · low_level_control(oracle|classical|
learned) · steps_or_tokens_per_episode · latency_per_step · n_seeds_reported · reproducible(y/n)`

The `in_domain_data_touched` and `what_was_pretrained` columns are the point of the whole exercise:
almost every "training-free" agent still leans on a waypoint predictor, a detector, or CLIP weights
trained on data that overlaps the target domain. Recording it is what makes Table VI a contribution
rather than a summary.

Keep it as `corpus.csv` in this folder; the LaTeX tables get generated from it, never typed by hand.

---

## 9. Expected volume (plan your time)

Q1 alone will return roughly a few hundred records for 2023+; Q2/Q3 push raw identification to
~1500–3000 with heavy overlap. After dedup and title/abstract screening expect **150–300**
full-text candidates and a final corpus of **~120–200** papers — the right size for a
25–35 page IEEE Access survey.
