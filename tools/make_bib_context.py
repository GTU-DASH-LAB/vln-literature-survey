#!/usr/bin/env python3
"""Bibliography for works the survey must cite but the harvest window excludes.

The corpus starts at 2023, so R2R, Habitat, CLIP and the other foundations are
absent from refs.bib by construction. Rather than type their metadata from
memory -- which is how wrong citations get into surveys -- resolve every one
through the Semantic Scholar title endpoint and write only what came back.
Anything that fails to resolve is reported, never guessed.

Writes latex/refs_context.bib. Keys are prefixed nothing special; they follow
the same author+year+word convention as refs.bib.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S2 = "https://api.semanticscholar.org/graph/v1/paper/search/match"
FIELDS = "title,year,venue,authors,externalIds,publicationVenue,publicationTypes"

# Titles only. Everything else is fetched.
WANTED = [
    "Vision-and-Language Navigation: Interpreting visually-grounded navigation instructions in real environments",
    "Room-Across-Room: Multilingual Vision-and-Language Navigation with Dense Spatiotemporal Grounding",
    "REVERIE: Remote Embodied Visual Referring Expression in Real Indoor Environments",
    "SOON: Scenario Oriented Object Navigation with Graph-based Exploration",
    "Vision-and-Dialog Navigation",
    "Beyond the Nav-Graph: Vision-and-Language Navigation in Continuous Environments",
    "Stay on the Path: Instruction Fidelity in Vision-and-Language Navigation",
    "General Evaluation for Instruction Conditioned Navigation using Dynamic Time Warping",
    "On Evaluation of Embodied Navigation Agents",
    "Matterport3D: Learning from RGB-D Data in Indoor Environments",
    "Habitat: A Platform for Embodied AI Research",
    "Habitat-Matterport 3D Dataset (HM3D): 1000 Large-scale 3D Environments for Embodied AI",
    "AI2-THOR: An Interactive 3D Environment for Visual AI",
    "ProcTHOR: Large-Scale Embodied AI using Procedural Generation",
    "Learning Transferable Visual Models From Natural Language Supervision",
    "BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models",
    "Visual Instruction Tuning",
    "Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection",
    "Segment Anything",
    "History Aware Multimodal Transformer for Vision-and-Language Navigation",
    "Think Global, Act Local: Dual-scale Graph Transformer for Vision-and-Language Navigation",
    "A Recurrent Vision-and-Language BERT for Navigation",
    "ZSON: Zero-Shot Object-Goal Navigation using Multimodal Goal Embeddings",
    "CoWs on Pasture: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation",
    "ESC: Exploration with Soft Commonsense Constraints for Zero-shot Object Navigation",
    "L3MVN: Leveraging Large Language Models for Visual Target Navigation",
    "CLIP-Nav: Using CLIP for Zero-Shot Vision-and-Language Navigation",
    "LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action",
    "Code as Policies: Language Model Programs for Embodied Control",
    "Do As I Can, Not As I Say: Grounding Language in Robotic Affordances",
    "Visual Language Maps for Robot Navigation",
    "ConceptFusion: Open-set Multimodal 3D Mapping",
    "ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning",
    "Open-vocabulary Queryable Scene Representations for Real World Planning",
    "NavGPT: Explicit Reasoning in Vision-and-Language Navigation with Large Language Models",
    "March in Chat: Interactive Prompting for Remote Embodied Referring Expression",
    "LangNav: Language as a Perceptual Representation for Navigation",
]

STOP = {"a","an","the","of","for","and","in","on","with","to","via","using","from","as","is","are"}

def get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gtu-vln-survey/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            w = min(60, 5 * 2 ** i)
            print(f"    HTTP {e.code}, retry in {w}s", file=sys.stderr); time.sleep(w)
        except Exception as e:
            print(f"    {e}, retry", file=sys.stderr); time.sleep(5)
    return None

def key(authors, year, title):
    sur = "anon"
    if authors:
        sur = re.sub(r"[^a-z]", "", authors[0].get("name", "").split()[-1].lower()) or "anon"
    w = [x for x in re.findall(r"[a-z0-9]+", title.lower()) if x not in STOP]
    return f"{sur}{year}{w[0] if w else 'x'}"

def esc(s):
    return (s or "").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")

def main():
    out, seen, missing = [], set(), []
    for t in WANTED:
        q = urllib.parse.urlencode({"query": t, "fields": FIELDS})
        d = get(f"{S2}?{q}")
        time.sleep(1.2)
        m = (d or {}).get("data") or []
        if not m:
            print(f"!! unresolved: {t}", file=sys.stderr); missing.append(t); continue
        p = m[0]
        au = p.get("authors") or []
        yr = p.get("year") or ""
        k = key(au, yr, p.get("title") or t)
        n = 0
        while k in seen:
            n += 1; k = key(au, yr, p.get("title") or t) + chr(ord("a") + n)
        seen.add(k)
        names = " and ".join(a.get("name", "") for a in au[:12])
        if len(au) > 12:
            names += " and others"
        ext = p.get("externalIds") or {}
        venue = p.get("venue") or (p.get("publicationVenue") or {}).get("name") or "arXiv preprint"
        fields = [f"  author  = {{{esc(names)}}}",
                  f"  title   = {{{{{esc(p.get('title') or t)}}}}}",
                  f"  year    = {{{yr}}}"]
        if "arXiv" in venue or venue == "arXiv preprint":
            fields.append(f"  journal = {{arXiv preprint arXiv:{ext.get('ArXiv','')}}}")
            typ = "article"
        else:
            fields.append(f"  booktitle = {{{esc(venue)}}}")
            typ = "inproceedings"
        if ext.get("DOI"):
            fields.append(f"  doi     = {{{ext['DOI']}}}")
        if ext.get("ArXiv") and typ == "inproceedings":
            fields.append(f"  note    = {{arXiv:{ext['ArXiv']}}}")
        out.append(f"@{typ}{{{k},\n" + ",\n".join(fields) + "\n}\n")
        print(f"  {k:<24} {yr}  {venue[:44]}")
    p = os.path.join(ROOT, "latex", "refs_context.bib")
    with open(p, "w", encoding="utf-8") as f:
        f.write("% Generated by tools/make_bib_context.py -- do not edit by hand.\n"
                "% Foundational works outside the 2023+ harvest window. Metadata comes\n"
                "% from the Semantic Scholar title-match endpoint, not from memory.\n\n")
        f.write("\n".join(out))
    print(f"\nwrote {len(out)} entries -> {p}")
    if missing:
        print("UNRESOLVED (cite by name in prose, or add by hand after checking):")
        for t in missing:
            print("  -", t)

if __name__ == "__main__":
    main()
