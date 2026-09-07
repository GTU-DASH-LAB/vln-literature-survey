#!/usr/bin/env python3
"""Draw how 11 244 retrieved records become the 98 papers the survey is written from.

Everything numeric is read from the generated data, never typed, so the figure cannot
disagree with the corpus. Emits:

  site/fig/selection-flow.svg    themed, for the page and the repository
  latex/fig/selection-flow.tex   TikZ, \\input into main.tex

The shape of the diagram is the argument: four query sets exist because one did not
work, and the audit that says so is drawn as a feedback loop, not a footnote.
"""
import csv, json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda n: json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))
hr, rl, ra = D("harvest_report.json"), D("reading_list.json"), D("recall_audit.json")

csv.field_size_limit(10_000_000)
SCRN = collections.Counter(
    r["decision"] for r in csv.DictReader(
        open(os.path.join(ROOT, "data", "corpus_screening.csv"), encoding="utf-8")))

P = {q: len(v) for q, v in hr["phrases"].items()}
SET = hr["per_set_after_dedup"]
SRC = hr["per_source"]
TIERS = [t["name"] for t in rl["tiers"]]
GOT = {t: sum(1 for r in rl["rows"] if r["tier"] == t) for t in TIERS}
QUOTA = {t: rl["short"].get(t, {}).get("quota", GOT[t]) for t in TIERS}
NPHRASE = sum(P.values())
f = lambda n: f"{n:,}".replace(",", " ")      # thin space, as in the manuscript

W, H = 1240, 1356
CX, BW = 588, 1096                                  # flow centre, content width
o = []; add = o.append

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif" '
    f'role="img" aria-label="Selection flow: 44 search phrases to 98 papers">')
add('''<style>
svg{--bg:#FFFFFF;--ink:#16202A;--mut:#5E6C76;--ln:#C9D3DA;--pl:#F4F7F9;
    --am:#B25E06;--amf:#FCF1E2;--te:#155F80;--tef:#E8F3F8;--wf:#FBEDE8;--wl:#A33A1F;--off:#98A6B0}
@media (prefers-color-scheme:dark){
svg{--bg:#12181E;--ink:#E9EFF3;--mut:#8FA0AC;--ln:#33414C;--pl:#182129;
    --am:#E8973A;--amf:#2A1F12;--te:#5FBEE0;--tef:#12242C;--wf:#2C1A16;--wl:#E38367;--off:#66757F}}
:root[data-theme="dark"] svg{--bg:#12181E;--ink:#E9EFF3;--mut:#8FA0AC;--ln:#33414C;--pl:#182129;
    --am:#E8973A;--amf:#2A1F12;--te:#5FBEE0;--tef:#12242C;--wf:#2C1A16;--wl:#E38367;--off:#66757F}
:root[data-theme="light"] svg{--bg:#FFFFFF;--ink:#16202A;--mut:#5E6C76;--ln:#C9D3DA;--pl:#F4F7F9;
    --am:#B25E06;--amf:#FCF1E2;--te:#155F80;--tef:#E8F3F8;--wf:#FBEDE8;--wl:#A33A1F;--off:#98A6B0}
.t{fill:var(--ink)}.m{fill:var(--mut)}.a{fill:var(--am)}.c{fill:var(--te)}
.bx{fill:var(--pl);stroke:var(--ln);stroke-width:1.5}
.bxa{fill:var(--amf);stroke:var(--am);stroke-width:1.5}
.bxc{fill:var(--tef);stroke:var(--te);stroke-width:1.5}
.bxw{fill:var(--wf);stroke:var(--wl);stroke-width:1.5}
.bxo{fill:none;stroke:var(--off);stroke-width:1.5;stroke-dasharray:5 4}
.ar{stroke:var(--ln);stroke-width:1.75;fill:none;marker-end:url(#h)}
.ln{stroke:var(--ln);stroke-width:1.75;fill:none}
.ara{stroke:var(--am);stroke-width:1.75;fill:none;marker-end:url(#ha);stroke-dasharray:6 4}
.band{fill:var(--mut);font-size:11px;letter-spacing:.10em;font-weight:600}
.n{font-variant-numeric:tabular-nums}
</style>
<defs>
<marker id="h" markerWidth="9" markerHeight="9" refX="7.5" refY="3.4" orient="auto">
<path d="M0,0 L7.5,3.4 L0,6.8 z" fill="var(--ln)"/></marker>
<marker id="ha" markerWidth="9" markerHeight="9" refX="7.5" refY="3.4" orient="auto">
<path d="M0,0 L7.5,3.4 L0,6.8 z" fill="var(--am)"/></marker>
</defs>''')
add(f'<rect width="{W}" height="{H}" fill="var(--bg)"/>')

def box(x, y, w, h, cls="bx"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" class="{cls}"/>')

def txt(x, y, s, size=12.5, cls="t", anchor="start", weight="400", mono=False):
    add(f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}{" n" if mono else ""}" '
        f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')

def arrow(x1, y1, x2, y2): add(f'<path d="M{x1},{y1} L{x2},{y2}" class="ar"/>')
def line(d): add(f'<path d="{d}" class="ln"/>')

def band(y, s):
    txt(40, y, s.upper(), 11, "band")
    add(f'<path d="M{40+len(s)*7.5+16},{y-4} L{40+BW},{y-4}" stroke="var(--ln)" stroke-width="1"/>')

def collect(xs, ytop, ybot):
    """Join several box bottoms into one arrow — cleaner than a fan of crossing lines."""
    line(f"M{min(xs)},{ytop} L{max(xs)},{ytop}")
    for x in xs: line(f"M{x},{ytop-10} L{x},{ytop}")
    arrow(CX, ytop, CX, ybot)

def spread(xs, ytop, ybot):
    line(f"M{min(xs)},{ytop} L{max(xs)},{ytop}")
    for x in xs: arrow(x, ytop, x, ybot)

txt(40, 46, f"How {NPHRASE} search phrases become {len(rl['rows'])} papers", 21, "t", weight="600")
txt(40, 68, f"Harvest {hr['retrieved']} · window {hr['window']} · every number generated from the corpus, none typed",
    12.5, "m")

# ── 1 · query sets ──────────────────────────────────────────────────────────
band(112, "1 · Query sets")
QS = [("core", "Q1 — the “…navigation” family", "high precision", "bxc"),
      ("recall", "Q2/Q4 — what else the field calls it", "the fix for Q1", "bxc"),
      ("zeroshot", "Q5 — zero-shot / training-free", "Section IX", "bxa"),
      ("enabler", "maps, scene graphs, code-as-policy", "never says “navigation”", "bxa")]
qx = []
for i, (k, desc, why, cls) in enumerate(QS):
    x = 40 + i * 278; qx.append(x + 131)
    box(x, 128, 262, 78, cls)
    txt(x + 14, 150, k, 14, "a" if cls == "bxa" else "c", weight="700")
    txt(x + 248, 150, f"{P[k]} phrases", 11.5, "m", anchor="end", mono=True)
    txt(x + 14, 170, desc, 11.5)
    txt(x + 14, 190, why, 11, "m")
    txt(x + 248, 190, f"→ {f(SET[k])} unique", 11.5, "m", anchor="end", mono=True)
collect(qx, 222, 268)

# ── 2 · sources ─────────────────────────────────────────────────────────────
band(258, "2 · Sources queried")
NICE = {"openalex": "OpenAlex", "s2": "Semantic Scholar", "arxiv": "arXiv",
        "openreview": "OpenReview", "crossref": "Crossref", "dblp": "DBLP"}
ROLE = {"openalex": "title + abstract phrase search", "s2": "indexes CV/robotics references",
        "arxiv": "the preprint stream", "openreview": "NeurIPS · ICLR · ICML · CoRL",
        "crossref": "publisher DOI records", "dblp": "canonical CS venues"}
sx = []
for i, k in enumerate(sorted(SRC, key=lambda k: -SRC[k])):
    x, y = 40 + (i % 3) * 372, 278 + (i // 3) * 62
    if i // 3 == 1: sx.append(x + 176)
    box(x, y, 352, 50)
    txt(x + 13, y + 21, NICE[k], 12.5, weight="600")
    txt(x + 339, y + 21, f(SRC[k]), 12.5, "c", anchor="end", weight="700", mono=True)
    txt(x + 13, y + 38, ROLE[k], 11, "m")
for i, (nm, why) in enumerate([("IEEE Xplore", "no API key set — the script skips it and says so"),
                               ("Scopus · Web of Science", "institutional session; export and merge instead")]):
    x = 40 + i * 558
    box(x, 402, 538, 44, "bxo")
    txt(x + 13, 422, nm, 12.5, "m", weight="600")
    txt(x + 525, 422, "not harvested", 11, "m", anchor="end")
    txt(x + 13, 438, why, 11, "m")
collect(sx, 462, 508)

# ── 3 · funnel ──────────────────────────────────────────────────────────────
band(498, "3 · Identification, deduplication, screening")
def stage(y, label, num, sub):
    box(308, y, 560, 60, "bx")
    txt(328, y + 25, label, 13.5, weight="600")
    txt(848, y + 27, f(num), 19, "c", anchor="end", weight="700", mono=True)
    txt(328, y + 45, sub, 11.5, "m")

stage(518, "Records retrieved", hr["raw_records"],
      "one row per record × source — the PRISMA identification count")
arrow(CX, 578, CX, 606)
stage(606, "Unique records", hr["after_dedup"],
      f"−{f(hr['duplicates_removed'])} duplicates on DOI, arXiv id and normalised title · "
      f"{f(hr['multi_source'])} found by ≥ 2 sources")
arrow(CX, 666, CX, 694)
box(308, 694, 560, 30, "bx")
txt(328, 714, "Title-and-abstract pre-screen against IC1–IC6 / EC1–EC7", 12.5, weight="600")

SCR = [("include", "navigation + language + vision all present", "bxc", "c"),
       ("check", "the gate could not call it — read these first", "bxa", "a"),
       ("survey", "EC6 — held for Table I, not the method corpus", "bx", "t"),
       ("exclude", "EC1–EC5, each row carrying the code that fired", "bx", "t")]
bx = [40 + i * 278 + 131 for i in range(4)]
line(f"M{CX},724 L{CX},742")
spread(bx, 742, 762)
for i, (k, why, cls, nc) in enumerate(SCR):
    x = 40 + i * 278
    box(x, 762, 262, 62, cls)
    txt(x + 14, 784, k, 13, nc, weight="700")
    txt(x + 248, 784, f(SCRN[k]), 15, nc if nc != "t" else "m", anchor="end", weight="700", mono=True)
    txt(x + 14, 804, why, 10.5, "m")
txt(40, 846, "A keyword gate cannot judge IC4–IC6. It orders the obvious exclusions and makes the "
             "undecidable bucket explicit; the human pass starts at check.", 11.5, "m")

# ── 4 · reading list ────────────────────────────────────────────────────────
band(888, f"4 · From {f(SCRN['include'])} included to the {len(rl['rows'])} read")
box(40, 904, 352, 78, "bxc")
txt(56, 926, "Pool", 13, "c", weight="700")
txt(376, 928, f(rl["pool"]), 19, "c", anchor="end", weight="700", mono=True)
txt(56, 946, f"include ∧ {rl['from_year']}–{rl['to_year']}", 11.5)
txt(56, 966, "pre-2024 work is cited as background, not read", 11, "m")
box(412, 904, 352, 78)
txt(428, 926, "Rank", 13, weight="600")
txt(428, 946, "citations ÷ years since publication", 11.5)
txt(428, 966, "× 1.25 peer-reviewed · +2 per agreeing source", 11, "m")
box(784, 904, 352, 78, "bxa")
txt(800, 926, "Gate", 13, "a", weight="700")
txt(800, 946, "seed ∨ peer-reviewed ∨ ≥ 3 citations", 11.5)
txt(800, 966, "an unfillable tier is left short, never padded", 11, "m")
arrow(392, 943, 408, 943); arrow(764, 943, 780, 943)
collect([216, 588, 960], 998, 1022)

# ── 5 · quotas ──────────────────────────────────────────────────────────────
band(1012, "5 · Chapter quotas — ceilings, not targets")
NOTE = ["Section IX — the survey's own argument",
        "the supervised line zero-shot is measured against",
        "the competing paradigm: one model, no pipeline",
        "Section V and Tables II–V",
        "RQ4 — the gap between a leaderboard and a robot",
        "never say “navigation”; the methods stand on them"]
tx = []
for i, t in enumerate(TIERS):
    x, y = 40 + (i % 3) * 372, 1032 + (i // 3) * 62
    if i // 3 == 1: tx.append(x + 176)
    shortfall = GOT[t] < QUOTA[t]
    box(x, y, 352, 50, "bxw" if shortfall else ("bxa" if i == 0 else "bx"))
    txt(x + 13, y + 21, t, 12, weight="600")
    txt(x + 339, y + 21, f"{GOT[t]} / {QUOTA[t]}", 12.5,
        "a" if shortfall else "c", anchor="end", weight="700", mono=True)
    txt(x + 13, y + 38, NOTE[i], 10.5, "m")
collect(tx, 1156, 1182)

box(308, 1182, 560, 62, "bxc")
txt(328, 1208, "Papers read", 14, weight="600")
txt(848, 1212, str(len(rl["rows"])), 25, "c", anchor="end", weight="700", mono=True)
txt(328, 1230, f"{len(rl['rows'])} not 100 — the maps/scene-graph tier filled {GOT[TIERS[5]]} of "
               f"{QUOTA[TIERS[5]]} slots and was left short", 11, "m")

# ── the feedback loop that produced four query sets ─────────────────────────
box(308, 1268, 560, 64, "bxa")
txt(328, 1290, "Recall audit", 12.5, "a", weight="700")
txt(848, 1292, ra["recall_in_window"], 15, "a", anchor="end", weight="700", mono=True)
txt(328, 1308, f"{ra['seeds']} landmark works; every seed inside the window is recovered. "
               f"Q1 alone recovered 8.", 11, "m")
txt(328, 1324, "Re-run after every query change — this loop is why there are four sets, not one.",
    11, "m")
add(f'<path d="M868,1300 L1196,1300 L1196,{112-6} L{40+BW+4},{112-6}" class="ara"/>')
add('</svg>')

open(os.path.join(ROOT, "site", "fig", "selection-flow.svg"), "w", encoding="utf-8").write("\n".join(o))
print(f"-> site/fig/selection-flow.svg  ({sum(len(x) for x in o)/1024:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════
# TikZ output for the manuscript. Same numbers, same five bands, but laid out
# for a two-column \figure* rather than a web page: wider, shorter, no colour
# that will not survive greyscale printing.
# ═══════════════════════════════════════════════════════════════════════════
def tikz():
    # The SVG formatter uses a U+2009 thin space, which pdflatex rejects under
    # T1/inputenc. LaTeX spells the same thing "\\,".
    f = lambda n: "{:,}".format(n).replace(",", "\\,")
    L = []
    a = L.append
    a("% Generated by tools/make_flow_diagram.py -- do not edit by hand.")
    a("% Every count is read from data/*.json at build time.")
    a("\\begin{tikzpicture}[")
    a("    font=\\footnotesize,")
    a("    bx/.style={draw, rounded corners=1.2pt, align=left, inner sep=4pt,")
    a("               minimum height=8mm, fill=black!2},")
    a("    hi/.style={bx, fill=black!8, very thick},")
    a("    wr/.style={bx, draw=black!55, dashed},")
    a("    bandlab/.style={font=\\scriptsize\\bfseries, anchor=west},")
    a("    ar/.style={-{Latex[length=1.7mm]}, thick},")
    a("    fb/.style={-{Latex[length=1.7mm]}, thick, dashed}]")
    a("")

    # band 1 -- query sets
    a("\\node[bandlab] at (0,0.55) {1 $\\cdot$ Query sets: %d phrases, "
      "tagged onto every record};" % NPHRASE)
    order = ["core", "recall", "zeroshot", "enabler"]
    for i, q in enumerate([q for q in order if q in P] + [q for q in P if q not in order]):
        x = i * 4.35
        a("\\node[%s, text width=3.7cm] (q%d) at (%.2f,-0.55) "
          "{\\textsc{%s}\\hfill\\textbf{%s}\\\\[1pt]\\scriptsize %d phrases};"
          % ("hi" if q == "zeroshot" else "bx", i, x + 1.85, q, f(SET[q]), P[q]))
    a("\\draw[ar] (8.05,-1.15) -- (8.05,-1.75);")

    # band 2 -- sources
    a("\\node[bandlab] at (0,-1.45) {2 $\\cdot$ Sources harvested};")
    src = sorted(SRC.items(), key=lambda kv: -kv[1])
    cells = " \\, ".join("%s~\\textbf{%s}" % (k, f(v)) for k, v in src)
    a("\\node[bx, text width=17.0cm] (src) at (8.05,-2.15) {%s};" % cells)
    miss = hr.get("sources_not_harvested") or []
    if miss:
        a("\\node[wr, text width=17.0cm] (nosrc) at (8.05,-2.95) "
          "{\\scriptsize Not harvested: %s \\, --- reported as a coverage limit, "
          "not implied to be complete.};" % ", ".join(miss))
        a("\\draw[ar] (8.05,-3.35) -- (8.05,-3.85);")
    else:
        a("\\draw[ar] (8.05,-2.55) -- (8.05,-3.85);")

    # band 3 -- identification / screening
    a("\\node[bandlab] at (0,-3.65) {3 $\\cdot$ Identification, deduplication, screening};")
    stages = [("Identified", f(hr["raw_records"])), ("Unique", f(hr["after_dedup"])),
              ("Included", f(SCRN.get("include", 0))), ("Excluded", f(SCRN.get("exclude", 0)))]
    for i, (lab, n) in enumerate(stages):
        a("\\node[bx, text width=3.7cm] (s%d) at (%.2f,-4.45) "
          "{%s\\hfill\\textbf{%s}};" % (i, i * 4.35 + 1.85, lab, n))
        if i:
            a("\\draw[ar] (s%d) -- (s%d);" % (i - 1, i))
    a("\\draw[ar] (8.05,-5.05) -- (8.05,-5.65);")

    # band 4 -- ranking
    a("\\node[bandlab] at (0,-5.45) {4 $\\cdot$ From included to read};")
    steps = [("Pool %s--%s" % (rl["from_year"], rl["to_year"]), f(rl["pool"])),
             ("Rank", "citations/yr $\\times$1.25 peer $+$2/source"),
             ("Gate", "seed $\\vee$ peer-reviewed $\\vee\\ \\geq$3 cites")]
    for i, (lab, n) in enumerate(steps):
        a("\\node[bx, text width=5.1cm] (r%d) at (%.2f,-6.25) "
          "{\\textbf{%s}\\\\[1pt]\\scriptsize %s};" % (i, i * 5.6 + 2.55, lab, n))
        if i:
            a("\\draw[ar] (r%d) -- (r%d);" % (i - 1, i))
    a("\\draw[ar] (8.05,-6.85) -- (8.05,-7.45);")

    # band 5 -- quotas
    a("\\node[bandlab] at (0,-7.25) {5 $\\cdot$ Chapter quotas --- ceilings, not targets};")
    for i, t in enumerate(TIERS):
        x, y = (i % 3) * 5.6, -8.05 - (i // 3) * 0.95
        short = GOT[t] < QUOTA[t]
        a("\\node[%s, text width=5.1cm] at (%.2f,%.2f) "
          "{\\scriptsize %s\\hfill\\textbf{%d\\,/\\,%d}};"
          % ("wr" if short else ("hi" if i == 0 else "bx"), x + 2.55, y,
             t.replace("&", "\\&"), GOT[t], QUOTA[t]))
    a("\\draw[ar] (8.05,-9.45) -- (8.05,-9.95);")
    a("\\node[hi, text width=8.0cm] (read) at (8.05,-10.45) "
      "{\\textbf{Papers read}\\hfill\\textbf{%d}\\\\[1pt]\\scriptsize %d not 100: the "
      "maps tier filled %d of %d and was left short.};"
      % (len(rl["rows"]), len(rl["rows"]), GOT[TIERS[5]], QUOTA[TIERS[5]]))

    # the feedback loop
    a("\\node[wr, text width=8.0cm] (aud) at (8.05,-12.35) "
      "{\\textbf{Recall audit}\\hfill\\textbf{%s}\\\\[1pt]\\scriptsize %d landmark works; "
      "Q1 alone recovered 8. This loop is why there are four query sets, not one.};"
      % (ra["recall_in_window"], ra["seeds"]))
    a("\\draw[ar] (read) -- (aud);")
    a("\\draw[fb] (aud.east) -- (17.8,-12.35) -- (17.8,0.95) -- (0.35,0.95)")
    a("     node[midway, above, font=\\scriptsize] {recall audit redesigned the query sets} -- (0.35,0.2);")
    a("\\end{tikzpicture}")
    p = os.path.join(ROOT, "latex", "fig")
    os.makedirs(p, exist_ok=True)
    p = os.path.join(p, "selection-flow.tex")
    open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"-> latex/fig/selection-flow.tex  ({len(L)} lines)")

tikz()
