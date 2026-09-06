# Survey Outline — Vision-and-Language Navigation in the Era of Foundation Models

Target venue style: IEEE (IEEEtran / IEEE Access `ieeeaccess.cls`).
Working title (draft): *From Supervised Instruction Following to Zero-Shot Embodied Reasoning:
A Survey of Vision-and-Language Navigation with Large Language and Vision-Language Models (2023–2026)*

---

## 0. Choosing the survey *type* (pick one, state it in Sec. I)

| Type | What it commits you to | Fit for this topic |
|---|---|---|
| **A. Systematic Literature Review (SLR / PRISMA)** | Explicit protocol, reproducible queries, PRISMA flow diagram, inclusion/exclusion criteria, screening log | Rigorous, reviewer-proof; but VLN moves through arXiv, so a pure SLR under-covers 2025–2026 |
| **B. Taxonomy-driven narrative survey** | A defensible taxonomy figure + thematic chapters; no formal screening record | Standard for CV/robotics surveys; weaker methodology section |
| **C. Bibliometric / scientometric analysis** | Scopus/WoS exports → VOSviewer/Bibliometrix co-word, co-citation, country/venue maps | Nice extra chapter, thin as a whole paper |
| **D. Benchmark-centric comparative survey** | Reproduce/collect leaderboard numbers, unify metrics, comparative tables | High citation value, high effort |

**Recommended: A + B + a slice of C.** Run a PRISMA-style search so Sec. III is defensible,
organise the body by taxonomy (B), and add 2–3 bibliometric figures (C) as the "research
landscape" subsection. Reserve D for the evaluation chapter (Sec. X) rather than the whole paper.

---

## 1. Choosing the *organising axis* of the body

Three candidate axes — do **not** mix them at the same level, that is the most common
survey-structure failure:

1. **Pipeline / component axis** — perception → language grounding → planning → control.
2. **Method-paradigm axis** — seq2seq → transformer pretraining → LLM-as-planner →
   end-to-end VLA/MLLM policies.
3. **Task-setting axis** — discrete graph (R2R) → continuous (VLN-CE) → object/demand-driven →
   dialogue → outdoor/aerial → real robot.

**Recommended:** paradigm axis (2) as the primary section structure — it matches the
"last three years / LLM" framing — with the pipeline axis (1) used *inside* each paradigm
section as a fixed subsection template, and the task axis (3) expressed only through tables.

**Plus one cross-cutting axis — the supervision level.** Because zero-shot navigation is a
focus of this survey, every method in the corpus is also tagged along:

```
fully supervised  →  pretrain + finetune  →  few-shot / in-context  →  zero-shot / training-free
```

This is a *column* in the master table and its own section (Sec. IX), not a fourth branch of the
main taxonomy tree. Keeping it orthogonal is what lets you say "here is the zero-shot version of
each paradigm" instead of duplicating the taxonomy.

---

## 2. Proposed section flow (IEEE numbering)

**I. Introduction**
- 1.1 Motivation: language as the interface to mobile robots
- 1.2 Why now: post-2023 shift from task-specific VLN models to foundation-model agents, and the
      parallel shift from *training on R2R* to *prompting an off-the-shelf model*
- 1.3 Scope: camera-based (RGB/RGB-D/panoramic) navigation driven by natural language
- 1.4 Comparison with existing surveys (Table I: survey, year, period covered, LLM coverage,
      **zero-shot coverage**, real-robot coverage, # papers) → state the *gap* this survey fills
- 1.5 Contributions (4–5 bullets; one of them: *a unified definition and audit of what
      "zero-shot" actually means across the VLN literature*)
- 1.6 Paper organisation (+ Fig. 1)

**II. Background and Problem Formulation**
- 2.1 Formal definition: POMDP ⟨S, A, O, T, R⟩ with an instruction conditioning variable
- 2.2 Observation space: monocular vs. panoramic vs. RGB-D vs. multi-camera
- 2.3 Action space: discrete panoramic graph vs. continuous velocity/waypoint vs. low-level control
- 2.4 Task family: R2R, RxR, REVERIE, SOON, CVDN, Touchdown, VLN-CE, ObjectNav, demand-driven,
      social/aerial navigation — and how they differ formally
- 2.5 Generalisation settings: seen vs. unseen split, unseen environment, unseen instruction style,
      unseen object category, unseen embodiment → *forward-reference to Sec. IX.A*
- 2.6 Terminology and abbreviations table (VLN, VLM, MLLM, VLA, BEV, SPL, nDTW …)

**III. Review Methodology**
- 3.1 Research questions (RQ1–RQ6)
- 3.2 Databases and rationale
- 3.3 Search strings per database
- 3.4 Inclusion / exclusion criteria
- 3.5 Screening pipeline + PRISMA flow diagram (Fig. 2)
- 3.6 Snowballing (backward + forward)
- 3.7 Research landscape: publications/year, venue distribution, keyword co-occurrence map
      (Figs. 3–5); include a *"zero-shot" term-frequency-over-time* curve — it makes the
      motivation for Sec. IX empirical rather than rhetorical
- 3.8 Threats to validity / limitations of the review

**IV. Taxonomy** — one full-page figure (Fig. 6) + a paragraph defining each branch and the
criterion that separates siblings. Every later section maps 1:1 onto a branch. Supervision level
is drawn as a **colour/shading overlay** on the tree, not as a branch.

**V. Environments, Datasets and Simulators**
- 5.1 Photorealistic scene datasets (Matterport3D, HM3D, ScanNet, Gibson)
- 5.2 Simulators (Habitat 2/3, AI2-THOR/ProcTHOR, Isaac Sim/Isaac Lab, Gazebo, AirSim/aerial)
- 5.3 Instruction corpora and their generation (human vs. template vs. LLM-synthesised)
- 5.4 Scale/realism/licence comparison table (Table II)
- 5.5 Data augmentation and synthetic environment generation
- 5.6 Benchmarks that specifically target generalisation (open-vocabulary object sets,
      cross-dataset splits, lifelong/multi-goal benchmarks)

**VI. Visual Perception and Scene Representation**
- 6.1 Frame-level encoders: CNN → ViT → CLIP/SigLIP/DINOv2 features
- 6.2 Panoramic vs. monocular observation and the field-of-view trade-off
- 6.3 Depth, point clouds and geometry-aware features
- 6.4 Map representations: metric occupancy, semantic maps, BEV, topological graphs,
      3D scene graphs, implicit/neural fields
- 6.5 **Open-vocabulary and language-queryable maps** — the main structural enabler of zero-shot
      navigation; CLIP-feature-fused maps, open-vocabulary 3D scene graphs, value/affordance maps
- 6.6 Memory: episodic buffers, history tokens, external memory, map-as-memory

**VII. Language Understanding and Cross-Modal Grounding**
- 7.1 Instruction decomposition into sub-goals / landmark–action pairs
- 7.2 Cross-modal attention and vision–language alignment objectives
- 7.3 Open-vocabulary grounding with CLIP-style and detector-based models
- 7.4 Spatial and relational language ("behind", "second door on the left")
- 7.5 Dialogue, clarification questions and ambiguous instructions

**VIII. Learned Navigation Policies** *(same subsection template for each paradigm:
idea → representative works → inputs/outputs → training signal → strengths → failure modes)*
- 8.1 Pre-foundation baselines: seq2seq, attention, RL/IL hybrids *(brief, for continuity)*
- 8.2 Vision-language pretraining agents (VLN-BERT, HAMT, DUET-style dual-scale graphs)
- 8.3 MLLM/VLM fine-tuned as policy — video-based navigation policies, VLA models transferred
      to navigation, action tokenisation
- 8.4 Hierarchical & modular learned systems — high-level planner + learned local policy
- 8.5 LLM-augmented *training* — instruction synthesis, reward shaping, self-training,
      distillation of an LLM teacher into a small deployable policy
- 8.6 Cross-cutting: uncertainty, backtracking, replanning, error recovery
- 8.7 Comparative summary table (Table III: method, backbone, obs. space, action space, map,
      **supervision level**, benchmark, SR/SPL)

**IX. Zero-Shot and Training-Free Navigation** ← *dedicated chapter*

- **9.1 What "zero-shot" means in VLN — a definitional taxonomy.**
  The term is used for at least five distinct claims, and papers routinely compare across them:
  - **ZS-1 Task-level / training-free** — no training on any VLN dataset; an off-the-shelf
    LLM/VLM is prompted at inference. The strongest claim.
  - **ZS-2 Open-vocabulary goal** — the agent handles object/goal categories never seen at
    training time (the usual claim in zero-shot ObjectNav).
  - **ZS-3 Cross-dataset / cross-task transfer** — trained on one benchmark, evaluated on another
    without fine-tuning (e.g. R2R → REVERIE, discrete → continuous).
  - **ZS-4 Cross-environment** — unseen scenes only. *Note: the standard `val-unseen` split is
    NOT zero-shot;* several papers imply it is. Worth stating plainly.
  - **ZS-5 Cross-embodiment / sim-to-real** — policy applied to a robot or morphology it was
    never trained on.
  → **Table VI: claim audit.** One row per zero-shot paper: which sense it claims, what it
  actually trained on (including CLIP/BLIP pretraining, which is rarely acknowledged), and
  whether any component saw in-domain data. This table alone is a citable contribution.

- **9.2 Training-free LLM-as-planner agents.** The dominant recipe: observation → captioner /
  open-vocab detector → textual scene description → LLM selects the next viewpoint or sub-goal →
  repeat. Cover the design choices: how the panorama is verbalised, how history is carried,
  how the action space is presented to the LLM, how invalid actions are handled.

- **9.3 Open-vocabulary perception as the enabler.** CLIP-based similarity, open-vocab detection
  and segmentation, VLM-produced value maps, language-queryable maps and 3D scene graphs.
  This is where Sec. 6.5 pays off.

- **9.4 Frontier-based exploration + semantic scoring.** The standard zero-shot ObjectNav
  architecture: classical frontier exploration for *where can I go*, foundation-model scoring for
  *where should I go*. Discuss why this modular split works without training.

- **9.5 Prompting and reasoning strategies.** Chain-of-thought spatial reasoning, ReAct-style
  act–observe loops, self-consistency, multi-expert / discussion agents, map-guided prompting,
  memory summarisation in the prompt, self-correction and backtracking prompts.

- **9.6 Code-as-policy and tool use.** LLM emits executable plans or calls perception/navigation
  APIs; composition of independently trained modules with no joint training.

- **9.7 The middle ground.** Few-shot in-context learning, retrieval-augmented navigation,
  test-time adaptation, and the counter-trend: **distilling zero-shot LLM agents into small
  supervised policies** — cheaper, faster, but loses the open-vocabulary property. Discuss the
  trade-off explicitly; it is the honest conclusion of the chapter.

- **9.8 Open-source vs. closed-model agents.** GPT-4/Gemini-based agents vs. open-weight
  LLM/VLM agents; the reproducibility problem when a closed model version is deprecated and the
  reported numbers can never be reproduced.

- **9.9 How zero-shot compares with supervised SOTA.**
  **Table VII:** for each benchmark (R2R, R2R-CE, REVERIE, RxR, ObjectNav-HM3D/MP3D), report
  supervised SOTA vs. best zero-shot, per year → shows whether the gap is closing.
  Then the cost axis the leaderboards hide: tokens/API cost per episode, inference latency per
  step, on-board feasibility. A zero-shot agent at 8 s/step is not deployable, and no benchmark
  table says so.

- **9.10 Failure modes specific to zero-shot agents.** Hallucinated landmarks and non-existent
  objects; the captioning bottleneck (information lost when pixels become text); weak metric and
  relational spatial reasoning; oscillation and loop behaviour without learned value functions;
  no low-level control (most zero-shot work assumes a graph or an oracle waypoint controller);
  prompt sensitivity and variance across runs — **and the fact that most papers report a single
  seed**.

**X. Evaluation: Metrics, Benchmarks and Results**
- 10.1 Metrics: SR, OSR, SPL, NE, TL, nDTW, SDTW, CLS, RGS/RGSPL — definitions and pitfalls
- 10.2 Leaderboard tables per benchmark
- 10.3 Cross-paper comparability problems (splits, backbones, pretraining data, closed models)
- 10.4 Human performance gap and what closed/did not close since 2023
- 10.5 Beyond success rate: efficiency, latency, energy, safety, instruction faithfulness
- 10.6 **What a fair zero-shot vs. supervised protocol would look like** — your proposal;
      surveys are allowed to make one normative recommendation, and this is a good one

**XI. From Simulation to the Real World**
- 11.1 Sim-to-real gap sources (visual, dynamic, layout)
- 11.2 Robot embodiments: wheeled, quadruped, humanoid, UAV
- 11.3 Onboard compute, quantisation, latency budgets for LLM/VLM inference
- 11.4 Reported real-world deployments and their evaluation protocols — note how many real-robot
      demos are zero-shot precisely *because* there is no real-world training data
- 11.5 Safety, human-aware and social navigation

**XII. Applications** — assistive navigation for visually impaired users, service/domestic robots,
warehouse and inspection, search and rescue, aerial/last-mile delivery, AR wayfinding.

**XIII. Open Challenges and Future Directions** *(mirror the RQs; 8–10 numbered challenges)*
- closing the zero-shot ↔ supervised gap without losing open-vocabulary generality;
- the perception bottleneck of text-mediated pipelines;
- spatial reasoning limits of current MLLMs;
- reproducibility of closed-model agents;
- latency and on-board deployment of foundation-model policies;
- long-horizon and lifelong navigation; data scarcity vs. synthetic-data collapse;
- unified benchmarks and a standard real-robot protocol;
- generalist embodied models vs. specialised navigation policies;
- multi-agent and human-in-the-loop navigation.

**XIV. Conclusion**

*(Appendix, optional: full query strings, per-database result counts, list of included papers.)*

---

## 3. Figures and tables to plan for now

| # | Content | Note |
|---|---|---|
| Fig. 1 | Paper organisation diagram | TikZ |
| Fig. 2 | PRISMA flow | TikZ, numbers from the search log |
| Fig. 3 | Publications per year per database | from Scopus/WoS CSV |
| Fig. 4 | Venue / research-area distribution | |
| Fig. 5 | Keyword co-occurrence map + "zero-shot" term frequency over time | VOSviewer |
| Fig. 6 | **Taxonomy tree**, with supervision level as a shading overlay | signature figure |
| Fig. 7 | Generic VLN system pipeline | perception→grounding→planning→control |
| Fig. 8 | Timeline of representative methods 2018–2026, supervised vs. zero-shot tracks | |
| **Fig. 9** | **Canonical zero-shot agent loop** — observation → open-vocab perception → text/value map → LLM reasoning → action → memory update | pairs with Sec. 9.2 |
| Table I | Comparison with prior VLN surveys (incl. a "zero-shot coverage" column) | justifies the paper |
| Table II | Datasets/simulators | |
| Table III | Method comparison, with a supervision-level column | landscape, two pages |
| Table IV | Metric definitions | |
| Table V | Real-robot deployments | |
| **Table VI** | **Zero-shot claim audit** (ZS-1…ZS-5, what was actually trained, backbone open/closed) | original contribution |
| **Table VII** | **Zero-shot vs. supervised SOTA per benchmark per year + cost/latency** | original contribution |

## 4. Practical writing order (not the reading order)

1. Sec. III (methodology) — because it fixes the corpus.
2. Sec. V + Sec. X tables — data you can collect mechanically.
3. **Table VI (zero-shot audit)** — build it while screening, not afterwards; you need to read the
   training details of each zero-shot paper anyway.
4. Fig. 6 taxonomy — freeze it before writing prose.
5. Secs. VI–IX — the bulk.
6. Secs. II, XI, XII.
7. Secs. XIII, XIV, then I last (the introduction promises what the paper actually delivers).
