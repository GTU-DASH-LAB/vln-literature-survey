#!/usr/bin/env python3
"""Resolve the zero-shot VLN seed list against the OpenAlex API.
OpenAlex is used instead of Semantic Scholar because the unauthenticated S2 pool
rate-limits (HTTP 429) immediately. All citation counts therefore come from a single
consistent source and can be cited as: OpenAlex, retrieved <date>.
Writes corpus_seeds.json + corpus_seeds.csv next to this file."""
import json, csv, time, urllib.parse, urllib.request, urllib.error, re, sys, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.openalex.org/works"

SEEDS = [
 ("A","NavGPT","zero-shot","ZS-1","R2R","9.2","NavGPT: Explicit Reasoning in Vision-and-Language Navigation with Large Language Models"),
 ("A","NavGPT-2","pretrain-finetune","-","R2R","9.2 (contrast)","NavGPT-2: Unleashing Navigational Reasoning Capability for Large Vision-Language Models"),
 ("A","MapGPT","zero-shot","ZS-1","R2R","9.2","MapGPT: Map-Guided Prompting with Adaptive Path Planning for Vision-and-Language Navigation"),
 ("A","DiscussNav","zero-shot","ZS-1","R2R","9.5","Discuss Before Moving: Visual Language Navigation via Multi-expert Discussions"),
 ("A","InstructNav","zero-shot","ZS-1,ZS-3","multi","9.2","InstructNav: Zero-shot Generalist Instruction Navigation"),
 ("A","Open-Nav","zero-shot","ZS-1","VLN-CE","9.8","Open-Nav: Exploring Zero-Shot Vision-and-Language Navigation in Continuous Environment with Open-Source LLMs"),
 ("A","March-in-Chat","zero-shot","ZS-1","REVERIE","9.5","March in Chat: Interactive Prompting for Remote Embodied Referring Expression"),
 ("A","CLIP-Nav","zero-shot","ZS-1","R2R","9.2","CLIP-Nav: Using CLIP for Zero-Shot Vision-and-Language Navigation"),
 ("A","LangNav","few-shot","ZS-3","R2R","9.2","LangNav: Language as a Perceptual Representation for Navigation"),

 ("B","CoW","zero-shot","ZS-1,ZS-2","ObjectNav","9.3","CoWs on Pasture: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation"),
 ("B","ZSON","zero-shot","ZS-2,ZS-3","ObjectNav","9.1","ZSON: Zero-Shot Object-Goal Navigation using Multimodal Goal Embeddings"),
 ("B","ESC","zero-shot","ZS-1,ZS-2","ObjectNav","9.4","ESC: Exploration with Soft Commonsense Constraints for Zero-shot Object Navigation"),
 ("B","L3MVN","zero-shot","ZS-1,ZS-2","ObjectNav","9.4","L3MVN: Leveraging Large Language Models for Visual Target Navigation"),
 ("B","VLFM","zero-shot","ZS-1,ZS-2","ObjectNav","9.4","VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation"),
 ("B","OpenFMNav","zero-shot","ZS-1,ZS-2","ObjectNav","9.3","OpenFMNav: Towards Open-Set Zero-Shot Object Navigation via Vision-Language Foundation Models"),
 ("B","SG-Nav","zero-shot","ZS-1,ZS-2","ObjectNav","9.3","SG-Nav: Online 3D Scene Graph Prompting for LLM-based Zero-shot Object Navigation"),
 ("B","VoroNav","zero-shot","ZS-1,ZS-2","ObjectNav","9.4","VoroNav: Voronoi-based Zero-shot Object Navigation with Large Language Model"),

 ("C","VLMaps","zero-shot","ZS-2","spatial goals","6.5","Visual Language Maps for Robot Navigation"),
 ("C","NLMap","zero-shot","ZS-2","planning","6.5","Open-vocabulary Queryable Scene Representations for Real World Planning"),
 ("C","ConceptFusion","zero-shot","ZS-2","mapping","6.5","ConceptFusion: Open-set Multimodal 3D Mapping"),
 ("C","ConceptGraphs","zero-shot","ZS-2","mapping","6.5","ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning"),
 ("C","HOV-SG","zero-shot","ZS-2","language nav","6.5","Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation"),

 ("D","LM-Nav","zero-shot","ZS-1,ZS-5","outdoor","9.6","LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action"),
 ("D","SayCan","zero-shot","ZS-1","manipulation","9.6","Do As I Can, Not As I Say: Grounding Language in Robotic Affordances"),
 ("D","Code as Policies","zero-shot","ZS-1","control","9.6","Code as Policies: Language Model Programs for Embodied Control"),

 ("E","NaVid","pretrain-finetune","-","VLN-CE","8.3","NaVid: Video-based VLM Plans the Next Step for Vision-and-Language Navigation"),
 ("E","NaVILA","pretrain-finetune","ZS-5","legged nav","8.3","NaVILA: Legged Robot Vision-Language-Action Model for Navigation"),
 ("E","Uni-NaVid","pretrain-finetune","-","multi","8.3","Uni-NaVid: A Video-based Vision-Language-Action Model for Unifying Embodied Navigation Tasks"),
 ("E","R2R","supervised","-","R2R","2.4","Vision-and-Language Navigation: Interpreting visually-grounded navigation instructions in real environments"),
 ("E","Rec-VLN-BERT","pretrain-finetune","-","R2R","8.2","A Recurrent Vision-and-Language BERT for Navigation"),
 ("E","HAMT","pretrain-finetune","-","R2R","8.2","History Aware Multimodal Transformer for Vision-and-Language Navigation"),
 ("E","DUET","pretrain-finetune","-","REVERIE","8.2","Think Global, Act Local: Dual-scale Graph Transformer for Vision-and-Language Navigation"),

 ("F","HM3D-OVON","benchmark","ZS-2","ObjectNav","5.6","HM3D-OVON: A Dataset and Benchmark for Open-Vocabulary Object Goal Navigation"),
 ("F","GOAT-Bench","benchmark","ZS-2","multi-goal","5.6","GOAT-Bench: A Benchmark for Multi-Modal Lifelong Navigation"),
 ("F","VLN-CE","benchmark","-","VLN-CE","5.6","Beyond the Nav-Graph: Vision-and-Language Navigation in Continuous Environments"),
]

def norm(t):
    return re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).strip()

def jaccard(a, b):
    A, B = set(norm(a).split()), set(norm(b).split())
    return len(A & B) / max(1, len(A | B))

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vln-survey-seed-resolver/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}", file=sys.stderr); time.sleep(5 * (i + 1))
        except Exception as e:
            print(f"  {type(e).__name__}: {e}", file=sys.stderr); time.sleep(4)
    return None

def search(title):
    q = re.sub(r'[,:;()\[\]]', ' ', title)
    q = re.sub(r'\s+', ' ', q).strip()
    u = f"{API}?filter=title.search:{urllib.parse.quote(q)}&per-page=12"
    d = get(u)
    if not (d or {}).get("results"):
        d = get(f"{API}?search={urllib.parse.quote(q)}&per-page=12")
    return (d or {}).get("results", []) or []

rows = []
for i, (grp, short, sup, zs, task, sec, title) in enumerate(SEEDS, 1):
    print(f"[{i}/{len(SEEDS)}] {short}", file=sys.stderr)
    # OpenAlex frequently holds several records for the same paper (arXiv preprint,
    # publisher version, proceedings entry) and splits the citation count between them.
    # Take every good title match, then keep the record with the HIGHEST cited_by_count
    # as the canonical one, and record how many duplicates were seen.
    cands = []
    for c in search(title):
        s = jaccard(title, c.get("title") or c.get("display_name"))
        if s >= 0.72:
            cands.append((s, c.get("cited_by_count") or 0, c))
    best, score, n_dupes, dupe_sum = None, 0.0, 0, 0
    if cands:
        n_dupes = len(cands)
        dupe_sum = sum(c[1] for c in cands)
        # prefer the highest-cited match; break ties on title similarity, then on
        # having a real publication venue rather than a bare preprint record
        cands.sort(key=lambda t: (t[1], t[0], bool(((t[2].get("primary_location") or {}).get("source") or {}))), reverse=True)
        score, _, best = cands[0]
    else:
        for c in search(title):
            s = jaccard(title, c.get("title") or c.get("display_name"))
            if s > score:
                best, score = c, s
    row = {"group": grp, "short": short, "supervision": sup, "zs_claim": zs,
           "task": task, "section": sec, "seed_title": title,
           "match_score": round(score, 3), "resolved": bool(best and score >= 0.45),
           "oa_records": n_dupes, "oa_records_citation_sum": dupe_sum}
    if best and score >= 0.45:
        auths = [(a.get("author") or {}).get("display_name", "") for a in (best.get("authorships") or [])]
        loc = (best.get("primary_location") or {}) or {}
        srcname = ((loc.get("source") or {}) or {}).get("display_name", "") or ""
        ids = best.get("ids") or {}
        arx = ""
        for lid in (best.get("locations") or []):
            lu = (lid.get("landing_page_url") or "")
            m = re.search(r'arxiv\.org/abs/([0-9.]+)', lu)
            if m: arx = m.group(1); break
        row.update({
            "title": best.get("display_name"),
            "year": best.get("publication_year"),
            "venue": srcname,
            "venue_type": (best.get("type") or ""),
            "citations": best.get("cited_by_count"),
            "authors": "; ".join([a for a in auths[:3] if a]) + (" et al." if len(auths) > 3 else ""),
            "n_authors": len(auths),
            "doi": (best.get("doi") or "").replace("https://doi.org/", ""),
            "arxiv": arx,
            "openalex": ids.get("openalex", ""),
            "url": loc.get("landing_page_url", "") or ids.get("openalex", ""),
            "oa": bool((best.get("open_access") or {}).get("is_oa")),
            "pdf": loc.get("pdf_url", "") or "",
            "referenced_works": len(best.get("referenced_works") or []),
        })
    else:
        row.update({"title": title, "year": None, "venue": "", "venue_type": "", "citations": None,
                    "authors": "", "n_authors": 0, "doi": "", "arxiv": "", "openalex": "",
                    "url": "", "oa": False, "pdf": "", "referenced_works": 0})
    rows.append(row)
    time.sleep(1.1)

meta = {"source": "OpenAlex", "retrieved": datetime.date.today().isoformat(),
        "n": len(rows), "resolved": sum(r["resolved"] for r in rows)}
with open(os.path.join(HERE, "corpus_seeds.json"), "w", encoding="utf-8") as f:
    json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=1)
cols = list(rows[0].keys())
with open(os.path.join(HERE, "corpus_seeds.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"\nDONE {meta}", file=sys.stderr)
