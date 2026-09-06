#!/usr/bin/env python3
"""Automated pre-screen of the harvested corpus against IC/EC (search_protocol.md §6).

This is a **pre-screen, not screening**. It fills the `decision` and `reason_code` columns
of `data/corpus_screening.csv` from title and abstract keywords so the 2 600-record corpus
arrives at the human pass already sorted, with the obvious exclusions grouped by the
protocol's own reason codes. Every row still needs a human decision; §7 requires it, and
the `check` bucket exists precisely because a keyword gate cannot judge the hard cases.

Decisions written:

  include        navigation + language + visual observation all present (IC4–IC6)
  check          the gate is not confident — read this one
  survey         a survey or review (EC6): collected separately for Table I
  exclude        with the reason code that fired (EC1–EC5)

  python3 tools/screen.py                # screen data/corpus_screening.csv in place
  python3 tools/screen.py --dry-run      # counts only, writes nothing
  python3 tools/screen.py --selftest

Existing non-empty decisions are preserved: once a human has judged a row, this script
never overwrites it. Delete the cell to re-screen it.
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # tools/ -> repository root
DATA = os.path.join(ROOT, "data")
PATH = os.path.join(DATA, "corpus_screening.csv")
csv.field_size_limit(10_000_000)

NAV = re.compile(r"\bnavigat\w+|wayfinding|path planning|route following|objectnav|"
                 r"object goal|point ?goal|image ?goal|\bvln\b|room-to-room|\br2r\b|\brxr\b|"
                 r"reverie|vln-ce|\bsoon\b|\bcvdn\b|touchdown|goat-bench|frontier explorat", re.I)
LANG = re.compile(r"natural language|instruction|language-guided|language guided|"
                  r"language-conditioned|language-driven|referring expression|dialog|"
                  r"vision-and-language|text-guided|open-vocabulary|open vocabulary|"
                  r"large language model|\bllm\b|vision-language model|\bvlm\b|\bmllm\b|"
                  r"prompt|semantic goal|free-form|\bgpt-?\d", re.I)
VIS = re.compile(r"\bvisual\b|\bvision\b|camera|\brgb\b|rgb-?d|egocentric|monocular|"
                 r"panoram\w+|\bimage\b|\bdepth\b|perception|observation|first-person|"
                 r"matterport|habitat|ai2-?thor|procthor|\bhm3d\b|\bgibson\b", re.I)
EMBODIED = re.compile(r"\brobot\w*|embodied|\bagent\w*|\buav\b|\bdrone\b|quadruped|"
                      r"mobile base|simulat\w+|real-world deployment", re.I)
DRIVING = re.compile(r"autonomous driving|self-driving|\bdriving\b|\blane\b|\bcarla\b|"
                     r"\bnuscenes\b|urban traffic|\bvehicle\b|\bego-?car\b", re.I)
SURVEY = re.compile(r"\bsurvey\b|\ba review\b|\breview of\b|systematic (?:literature )?review|"
                    r"\btaxonomy\b|\bcomprehensive review\b|\boverview of\b", re.I)
MANIP = re.compile(r"manipulat\w+|\bgrasp\w*|gripper|pick[- ]and[- ]place|dexterous|"
                   r"end[- ]effector|bimanual|tabletop", re.I)
ENABLER = re.compile(r"scene graph|semantic map|open-vocabulary map|3d map|slam|"
                     r"queryable|code as policies|language model program|scene representation", re.I)
ZS = re.compile(r"zero-shot|zero shot|training-free|training free|open-vocabulary|"
                r"open vocabulary|open-set|off-the-shelf|without fine-tuning|"
                r"in-context learning", re.I)
# "navigation" also means moving around a screen or a website; those agents are not embodied
GUI = re.compile(r"\bgui\b|graphical user interface|web agent|web navigation|browser|"
                 r"\bwebpage\b|\bwebsite\b|screenshot|\bui element|\bapp\b agent|"
                 r"\bandroid\b|\bwebarena\b|\bmind2web\b|\bminiwob\b|click.{0,12}button", re.I)
# indoor / embodied-robot setting — what separates VLN from a driving paper that
# happens to use the phrase "vision-language navigation"
INDOOR = re.compile(r"\bindoor\b|habitat|matterport|ai2-?thor|procthor|\bhm3d\b|\bgibson\b|"
                    r"household|home environment|quadruped|legged|wheelchair|"
                    r"\bdrone\b|\buav\b|aerial|\bmobile robot\b", re.I)

# the 3D scene an embodied agent moves through
SCENE3D = re.compile(r"\bindoor\b|\b3d\b|matterport|habitat|ai2-?thor|procthor|\bhm3d\b|"
                     r"\bgibson\b|real robot|mobile robot|\bdrone\b|\buav\b|quadruped|"
                     r"physical (?:world|environment)|embodied agent|\bslam\b|waypoint", re.I)

JUNK = re.compile(r"^(?:table of contents|front matter|back matter|author index|"
                  r"subject index|editorial|title page|proceedings of the|"
                  r"list of (?:reviewers|contributors))\b", re.I)

TASK = [("R2R", r"room-to-room|\br2r\b"), ("RxR", r"\brxr\b|room-across-room"),
        ("REVERIE", r"reverie"), ("CVDN", r"\bcvdn\b|cooperative vision-and-dialog"),
        ("SOON", r"\bsoon benchmark\b"), ("VLN-CE", r"vln-ce|continuous environment"),
        ("ObjectNav", r"objectnav|object goal navigation|object-goal navigation"),
        ("Touchdown", r"touchdown"), ("ALFRED", r"\balfred\b"),
        ("GOAT", r"goat-bench"), ("aerial", r"\buav\b|\bdrone\b|aerial")]

def nav_substantive(title, text):
    """Is navigation the subject, or just a word that turned up once?

    A manipulation paper that says "navigating the workspace", or a general MLLM
    benchmark that lists navigation among twenty tasks, matches the navigation
    vocabulary without being navigation work. Require the title, or repetition."""
    return bool(NAV.search(title)) or len(NAV.findall(text)) >= 2


def screen(row):
    """-> (decision, reason_code, task, zs_flag). Sees only title, abstract, venue."""
    title = row.get("title") or ""
    text = f"{title} {row.get('abstract') or ''} {row.get('venue') or ''}"
    sets = row.get("query_sets") or ""

    nav, lang, vis = bool(NAV.search(text)), bool(LANG.search(text)), bool(VIS.search(text))
    task = next((t for t, rx in TASK if re.search(rx, text, re.I)), "")
    zs = "candidate" if ZS.search(text) else ""

    if JUNK.match(title.strip()):
        return "exclude", "EC7", "", ""
    if SURVEY.search(title):
        return "survey", "EC6", task, zs
    # driving only excludes when nothing indoor-embodied is going on
    # EC5: driving is a different problem and a different community. A navigation phrase
    # in the title does not make an autonomous-vehicle dataset an embodied-navigation one.
    if (DRIVING.search(title) or len(DRIVING.findall(text)) >= 3) and not INDOOR.search(text):
        return "exclude", "EC5", "", zs
    # a GUI or web agent "navigates" a screen, not a 3D environment
    if GUI.search(text) and not SCENE3D.search(text):
        return "exclude", "EC4", "", zs
    if nav and not nav_substantive(title, text):
        nav = False                     # mentioned in passing, not the subject
    if not nav:
        # the enabler set is expected to lack the word: maps, scene graphs, code-as-policy
        if "enabler" in sets and ENABLER.search(text):
            return "check", "enabler", task, zs
        return "exclude", "EC3" if MANIP.search(text) else "EC4", "", zs
    if not lang:
        return "exclude", "EC1", task, zs
    if not vis:
        return "exclude", "EC2", task, zs
    if not EMBODIED.search(text):
        return "check", "no embodiment stated", task, zs
    if not (row.get("abstract") or "").strip():
        return "check", "no abstract retrieved", task, zs
    return "include", "", task, zs

def run(dry=False):
    with open(PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        cols = list(rows[0]) if rows else []
    counts, kept = {}, 0
    for r in rows:
        if (r.get("decision") or "").strip():      # a human already ruled on this row
            kept += 1
            counts[r["decision"] + " (kept)"] = counts.get(r["decision"] + " (kept)", 0) + 1
            continue
        d, code, task, zs = screen(r)
        r["decision"], r["reason_code"] = d, code
        if task: r["task"] = task
        if zs: r["zs_claim"] = zs
        label = d + (f" · {code}" if code else "")
        counts[label] = counts.get(label, 0) + 1
    if not dry:
        with open(PATH, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(rows)
    return rows, counts, kept

def selftest():
    d, c, t, z = screen({"title": "MapGPT: Map-Guided Prompting for VLN",
                         "abstract": "A zero-shot agent follows natural language instructions "
                                     "using RGB observations in Habitat.", "venue": "ACL"})
    assert (d, c, z) == ("include", "", "candidate"), (d, c, z)
    d, c, _, _ = screen({"title": "Cloth folding with a bimanual robot",
                         "abstract": "We grasp fabric.", "venue": ""})
    assert (d, c) == ("exclude", "EC3"), (d, c)
    d, c, _, _ = screen({"title": "Frontier exploration for mapping",
                         "abstract": "A robot explores with a depth camera, no language.",
                         "venue": ""})
    assert (d, c) == ("exclude", "EC1"), (d, c)
    d, c, _, _ = screen({"title": "doScenes: An Autonomous Driving Dataset with Natural "
                                  "Language Instruction for Vision-Language Navigation",
                         "abstract": "Autonomous vehicles must integrate human instructions "
                                     "into motion planning for driving.", "venue": "IEEE"})
    assert (d, c) == ("exclude", "EC5"), (d, c)
    d, c, _, _ = screen({"title": "EchoVLA: a robot manipulation policy",
                         "abstract": "Our arm grasps objects while navigating the workspace.",
                         "venue": "CoRL"})
    assert (d, c) == ("exclude", "EC3"), (d, c)
    d, c, _, _ = screen({"title": "ShowUI: One Vision-Language-Action Model for GUI Agents",
                         "abstract": "Our model navigates a webpage from a screenshot and clicks "
                                     "the button the instruction names.", "venue": "CVPR"})
    assert (d, c) == ("exclude", "EC4"), (d, c)
    d, c, _, _ = screen({"title": "A Survey of Vision-and-Language Navigation",
                         "abstract": "We review instruction-following agents.", "venue": ""})
    assert (d, c) == ("survey", "EC6"), (d, c)
    d, c, _, _ = screen({"title": "ConceptGraphs: Open-Vocabulary 3D Scene Graphs",
                         "abstract": "We build a queryable scene representation for robots.",
                         "venue": "ICRA", "query_sets": "enabler"})
    assert (d, c) == ("check", "enabler"), (d, c)
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    rows, counts, kept = run("--dry-run" in sys.argv)
    print(f"{len(rows)} records pre-screened" + (f", {kept} human decisions preserved" if kept else ""))
    for k in sorted(counts, key=lambda x: -counts[x]):
        print(f"  {k:<28} {counts[k]}")
    print("\nThis is a pre-screen. Every row still needs a human decision (§7)." +
          ("" if "--dry-run" in sys.argv else f"\nwrote {os.path.basename(PATH)}"))
