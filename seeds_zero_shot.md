# Seed Works — Zero-Shot / Training-Free Navigation

**Resolved.** Every entry below was matched against the OpenAlex API (venue, DOI, open access)
and re-counted through the Semantic Scholar batch endpoint. Citation counts are Semantic Scholar,
retrieved 2026-09-05 — all 35/35 rows from that one source, so the column is a
single comparable scale.

> **Why not OpenAlex counts.** OpenAlex does not index the reference lists of most CV and ML
> proceedings. It holds **61** citations for R2R against **1,922** on Semantic Scholar, and **21**
> for HAMT against **409**. Ranking this literature on OpenAlex would invert the order. Both
> figures are kept per row in `corpus_seeds.csv` (`citations_primary` vs `oa_citations`).

> **Still verify before citing.** Titles and venues were resolved automatically. Confirm each one
> in the database export before it becomes a reference. Entries before 2023 are **background**
> works — cited in text, excluded from the PRISMA corpus.

Machine-readable: `corpus_seeds.csv` / `corpus_seeds.json`. Interactive: `vln_survey_plan.html`.

## A. Training-free LLM-as-planner agents on VLN benchmarks
*Outline §9.2*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **NavGPT** | 2024 | AAAI Conference on Artificial Intelligence | 448 | zero-shot | ZS-1 |
| **InstructNav** | 2024 | Conference on Robot Learning | 216 | zero-shot | ZS-1,ZS-3 |
| **DiscussNav** | 2024 | IEEE International Conference on Robotics… | 159 | zero-shot | ZS-1 |
| **MapGPT** | 2024 | Annual Meeting of the Association for Com… | 152 | zero-shot | ZS-1 |
| **NavGPT-2** | 2024 | European Conference on Computer Vision | 134 | pretrain-finetune | - |
| **CLIP-Nav** | 2022 | arXiv.org | 99 | zero-shot | ZS-1 |
| **Open-Nav** | 2025 | IEEE International Conference on Robotics… | 77 | zero-shot | ZS-1 |
| **LangNav** | 2024 | NAACL-HLT | 64 | few-shot | ZS-3 |
| **March-in-Chat** | 2023 | IEEE International Conference on Computer… | 59 | zero-shot | ZS-1 |

## B. Zero-shot ObjectNav: frontier exploration + foundation-model scoring
*Outline §9.3–9.4*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **VLFM** | 2024 | IEEE International Conference on Robotics… | 393 | zero-shot | ZS-1,ZS-2 |
| **CoW** | 2023 | Computer Vision and Pattern Recognition | 339 | zero-shot | ZS-1,ZS-2 |
| **ZSON** | 2022 | Neural Information Processing Systems | 334 | zero-shot | ZS-2,ZS-3 |
| **ESC** | 2023 | International Conference on Machine Learn… | 268 | zero-shot | ZS-1,ZS-2 |
| **L3MVN** | 2023 | IEEE/RJS International Conference on Inte… | 265 | zero-shot | ZS-1,ZS-2 |
| **SG-Nav** | 2024 | Neural Information Processing Systems | 196 | zero-shot | ZS-1,ZS-2 |
| **OpenFMNav** | 2024 | NAACL-HLT | 122 | zero-shot | ZS-1,ZS-2 |
| **VoroNav** | 2024 | International Conference on Machine Learn… | 106 | zero-shot | ZS-1,ZS-2 |

## C. Open-vocabulary / language-queryable maps — the enabler
*Outline §6.5, 9.3*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **VLMaps** | 2023 | IEEE International Conference on Robotics… | 649 | zero-shot | ZS-2 |
| **ConceptGraphs** | 2024 | IEEE International Conference on Robotics… | 560 | zero-shot | ZS-2 |
| **ConceptFusion** | 2023 | Robotics: Science and Systems Conference | 424 | zero-shot | ZS-2 |
| **HOV-SG** | 2024 | Robotics: Science and Systems Conference | 309 | zero-shot | ZS-2 |
| **NLMap** | 2023 | IEEE International Conference on Robotics… | 260 | zero-shot | ZS-2 |

## D. Composition, code-as-policy, tool use
*Outline §9.6*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **SayCan** | 2022 | Conference on Robot Learning | 3608 | zero-shot | ZS-1 |
| **Code as Policies** | 2023 | IEEE International Conference on Robotics… | 1816 | zero-shot | ZS-1 |
| **LM-Nav** | 2022 | Conference on Robot Learning | 771 | zero-shot | ZS-1,ZS-5 |

## E. Contrast set — trained policies, needed for Table VII
*Outline §8.2–8.3*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **R2R** | 2018 | 2018 IEEE/CVF Conference on Computer Visi… | 1922 | supervised | - |
| **Rec-VLN-BERT** | 2021 | Computer Vision and Pattern Recognition | 478 | pretrain-finetune | - |
| **HAMT** | 2021 | Neural Information Processing Systems | 409 | pretrain-finetune | - |
| **DUET** | 2022 | Computer Vision and Pattern Recognition | 298 | pretrain-finetune | - |
| **NaVid** | 2024 | Robotics: Science and Systems Conference | 294 | pretrain-finetune | - |
| **NaVILA** | 2025 | Robotics | 263 | pretrain-finetune | ZS-5 |
| **Uni-NaVid** | 2025 | arXiv.org | 182 | pretrain-finetune | - |

## F. Benchmarks that stress generalisation
*Outline §5.6*

| Work | Year | Venue | Cited | Supervision | ZS claim |
|---|---:|---|---:|---|---|
| **VLN-CE** | 2020 | European Conference on Computer Vision | 622 | benchmark | - |
| **GOAT-Bench** | 2024 | Computer Vision and Pattern Recognition | 130 | benchmark | ZS-2 |
| **HM3D-OVON** | 2024 | IEEE/RJS International Conference on Inte… | 108 | benchmark | ZS-2 |

---

## How to use this file

1. Run each database query, then check that the result set contains groups A and B.
   Missing more than two of them means the query is too narrow — widen it and log the change.
2. Forward-snowball from **CoW, ZSON, VLFM, NavGPT and VLMaps** through Semantic Scholar
   *cited by*, restricted to 2023+. These five have the highest yield of new zero-shot work
   per citation edge.
3. Backward-snowball from the two or three most recent zero-shot survey and benchmark papers.
4. For every entry that survives screening, fill the **zero-shot sub-sheet** in
   `search_protocol.md` §8 — above all `what_was_pretrained` and `in_domain_data_touched`.
