#!/usr/bin/env python3
"""Bibliography for works the survey must cite but the included set excludes.

The corpus starts at 2023, so R2R, Habitat, CLIP and the other foundations are
absent from refs.bib by construction; so are the prior surveys, which screening
routes to decision=survey rather than include. Rather than type their metadata from
memory -- which is how wrong citations get into surveys -- resolve every one
through the Semantic Scholar title endpoint and write only what came back.
Anything that fails to resolve is reported, never guessed.

S2 is the index, not the last word. Its record sometimes carries the title a
survey had at v1 and lost at v5, and its year is sometimes the year the work
was first seen rather than the year of the venue it names. Both matter here:
Table I prints the year. So every record that carries an arXiv id is
cross-checked against arXiv (for the current title, and the v1 date) and
against the year DBLP encodes in its key, and every disagreement is printed.

Writes latex/refs_context.bib. Keys are prefixed nothing special; they follow
the same author+year+word convention as refs.bib.
"""
import csv, json, os, random, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S2 = "https://api.semanticscholar.org/graph/v1/paper/search/match"
FIELDS = ("title,year,venue,authors,externalIds,publicationVenue,"
          "publicationTypes,publicationDate,journal")
ARXIV = "http://export.arxiv.org/api/query?id_list="
CONF = re.compile(r"Conference|Symposium|Workshop|Proceedings|Meeting|Congress"
                  r"|\b(ACL|NAACL|EMNLP|COLING|CVPR|ICCV|ECCV|NeurIPS|ICML|ICLR"
                  r"|AAAI|IJCAI|ICRA|IROS|CoRL|RSS|WACV|BMVC|SIGGRAPH)\b")

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

    # Prior surveys. Screening routes reviews to decision=survey rather than
    # include, so they never reach reading_list.csv and cannot appear in
    # refs.bib -- but Table I compares against them, so they are resolved here.
    # Only the ones whose full text was read are listed; a comparison table
    # must not assert what a survey omits on the strength of its abstract.
    "Advances in Embodied Navigation Using Large Language Models: A Survey",
    "Vision-and-Language Navigation Today and Tomorrow: A Survey in the Era of Foundation Models",
    "A Survey on Vision-Language-Action Models for Embodied AI",
    "Multimodal Perception for Goal-oriented Navigation: A Survey",
    "Sensing, Social, and Motion Intelligence in Embodied Navigation: A Comprehensive Survey",
    "Safety of Embodied Navigation: A Survey",
    "A Comprehensive Survey and Systematic Real-World Evaluation of Embodied Vision-and-Language Navigation",
]

STOP = {"a","an","the","of","for","and","in","on","with","to","via","using","from","as","is","are"}

def get(url, tries=14):
    """S2's unauthenticated pool 429s a large fraction of requests at random,
    and the rejection is immediate rather than a sustained block: many short
    retries resolve far more titles than a few long ones. Only a run that
    resolves every title may overwrite the .bib, so patience here is what
    keeps the bibliography complete."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gtu-vln-survey/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            w = min(30, 2 ** i) + random.random()
            print(f"    HTTP {e.code}, retry in {w:.0f}s", file=sys.stderr); time.sleep(w)
        except Exception as e:
            print(f"    {e}, retry", file=sys.stderr); time.sleep(5)
    return None

def get_text(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gtu-vln-survey/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"    arxiv: {e}, retry", file=sys.stderr); time.sleep(6)
    return ""

def arxiv_meta(aid):
    """Current title and v1 date for an arXiv id, from arXiv itself."""
    x = get_text(f"{ARXIV}{aid}")
    m = re.search(r"<entry>(.*?)</entry>", x, re.S)
    if not m:
        return {}
    e = m.group(1)
    def f(tag):
        g = re.search(rf"<{tag}>(.*?)</{tag}>", e, re.S)
        return re.sub(r"\s+", " ", g.group(1)).strip() if g else ""
    return {"title": f("title"), "date": f("published")[:10],
            "jref": f("arxiv:journal_ref"), "doi": f("arxiv:doi")}

def dblp_year(dblp):
    """DBLP puts the venue year in its key -- conf/ijcai/WangHM25 -> 2025 --
    and curates it. Its arXiv mirror keys (journals/corr/abs-2407-07035) carry
    no year, and the pattern below deliberately does not match them."""
    m = re.match(r"^[a-z]+/[^/]+/[A-Za-z]+(\d{2})$", dblp or "")
    if not m:
        return None
    n = int(m.group(1))
    return 2000 + n if n < 80 else 1900 + n

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

    # refs.bib is generated independently from the same key convention, so a
    # 2024 Zhou NavGPT here collides with the 2024 Zhou NavGPT-2 there -- and
    # BibTeX answers a repeated key by dropping one of the two entries.
    rb = os.path.join(ROOT, "latex", "refs.bib")
    if os.path.exists(rb):
        with open(rb, encoding="utf-8") as f:
            seen |= set(re.findall(r"^@\w+\{([^,]+),", f.read(), re.M))
        print(f"  ({len(seen)} keys already taken by refs.bib)")
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
        ttl = p.get("title") or t
        ext = p.get("externalIds") or {}

        # An arXiv id may be absent from externalIds while the DOI encodes it.
        aid = ext.get("ArXiv")
        if not aid:
            d48 = re.match(r"10\.48550/arXiv\.(.+)$", ext.get("DOI") or "", re.I)
            aid = d48.group(1) if d48 else None

        # Cross-check against arXiv and DBLP. Print every disagreement: this
        # file is generated, so the run log is the only place a reader can see
        # what was corrected and why.
        if aid:
            ax = arxiv_meta(aid)
            time.sleep(3.0)
            if ax.get("title") and ax["title"].lower() != ttl.lower():
                print(f"    title: S2 {ttl!r} -> arXiv {ax['title']!r}")
                ttl = ax["title"]
            dy = dblp_year(ext.get("DBLP"))
            ay = int(ax["date"][:4]) if ax.get("date") else None
            if dy and yr and dy != yr:
                print(f"    year : S2 {yr} -> DBLP {dy} (venue year)")
                yr = dy
            elif ay and yr and yr < ay:
                print(f"    year : S2 {yr} -> arXiv v1 {ay} (S2 predates the preprint)")
                yr = ay

        # Type follows the venue, not the presence of a preprint: a journal
        # article cited as @inproceedings renders as "in IEEE Transactions...".
        pv = p.get("publicationVenue") or {}
        jn = (p.get("journal") or {}).get("name") or ""
        venue = jn or pv.get("name") or p.get("venue") or ""
        types = p.get("publicationTypes") or []

        # Proceedings titles state their own year, and it is the year the work
        # was published; S2 often carries the preprint's instead. This is how
        # R2R ends up cited as 2017 in half the literature -- CVPR 2018.
        vy = re.match(r"((?:19|20)\d{2})\b", venue.strip())
        if vy and yr and int(vy.group(1)) != yr:
            print(f"    year : S2 {yr} -> {vy.group(1)} (stated by the proceedings)")
            yr = int(vy.group(1))

        k = key(au, yr, ttl)
        n = 0
        while k in seen:
            n += 1; k = key(au, yr, ttl) + chr(ord("a") + n - 1)
        seen.add(k)
        names = " and ".join(a.get("name", "") for a in au[:12])
        if len(au) > 12:
            names += " and others"

        fields = [f"  author  = {{{esc(names)}}}",
                  f"  title   = {{{{{esc(ttl)}}}}}",
                  f"  year    = {{{yr}}}"]
        if not venue or "arxiv" in venue.lower():
            typ = "article"
            fields.append(f"  journal = {{arXiv preprint arXiv:{aid}}}" if aid
                          else "  journal = {arXiv preprint}")
            venue = f"arXiv:{aid}" if aid else "arXiv preprint"
        elif pv.get("type") == "conference" or "Conference" in types or CONF.search(venue):
            typ = "inproceedings"
            fields.append(f"  booktitle = {{{esc(venue)}}}")
        else:
            typ = "article"
            fields.append(f"  journal = {{{esc(venue)}}}")
        if ext.get("DOI"):
            fields.append(f"  doi     = {{{ext['DOI']}}}")
        if aid and not venue.startswith("arXiv"):
            fields.append(f"  note    = {{arXiv:{aid}}}")
        out.append(f"@{typ}{{{k},\n" + ",\n".join(fields) + "\n}\n")
        print(f"  {k:<24} {yr}  {venue[:44]}")
    p = os.path.join(ROOT, "latex", "refs_context.bib")

    # S2 rate-limits, and a run that 429s its way through half the list would
    # otherwise write a shorter file over a complete one -- which surfaces as
    # undefined citations in a build nobody connects to this script. Never
    # shrink the file; report and leave the old one in place instead.
    if os.path.exists(p):
        have = sum(1 for line in open(p, encoding="utf-8") if line.startswith("@"))
        if len(out) < have:
            print(f"REFUSING to write: resolved {len(out)} entries but "
                  f"{os.path.basename(p)} already holds {have}. Left untouched.",
                  file=sys.stderr)
            for t in missing:
                print("  unresolved:", t, file=sys.stderr)
            return 1

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
    sys.exit(main() or 0)
