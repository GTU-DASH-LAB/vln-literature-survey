#!/usr/bin/env python3
"""Make harvested BibTeX safe for pdflatex, idempotently.

Bibliographic APIs return display strings, not LaTeX: Crossref hands back
HTML tags inside titles, and Semantic Scholar hands back whatever Unicode
the publisher used. Both reach the .bib untouched and then either break the
build (U+21BB has no T1 slot) or render literally in the bibliography
(``<i>Cat-shaped Mug</i>''). This normalises both files in place.

Run after any harvest; re-running changes nothing.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["refs.bib", "refs_context.bib"]

# Unicode that either breaks T1 or should be real LaTeX punctuation.
CHARS = {
    "↻": r"$\circlearrowright$",   # VLN(reverse-arrow)BERT
    "–": "--", "—": "---", "‐": "-", "‑": "-",
    "“": "``", "”": "''", "‘": "`", "’": "'",
    "²": r"$^2$", "³": r"$^3$",
    "ü": r'\"{u}', "ö": r'\"{o}', "ä": r'\"{a}',
    "Ü": r'\"{U}', "Ö": r'\"{O}', "Ä": r'\"{A}',
    "ß": r"\ss{}",
    "é": r"\'{e}", "è": r"\`{e}", "ê": r"\^{e}",
    "á": r"\'{a}", "à": r"\`{a}", "â": r"\^{a}",
    "í": r"\'{i}", "ó": r"\'{o}", "ú": r"\'{u}",
    "ç": r"\c{c}", "ñ": r"\~{n}",
    "ı": r"\i{}", "ă": r"\u{a}", "ş": r"\c{s}",
    "ř": r"\v{r}", "ž": r"\v{z}", "š": r"\v{s}",
    "ł": r"\l{}", "ć": r"\'{c}", "å": r"\aa{}",
    "′": "'", " ": " ",
}
TAGS = re.compile(r"</?(?:i|b|em|strong|sub|sup|span|scp|inf)\s*/?>", re.I)
ENTS = {"&amp;": r"\&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'",
        "&nbsp;": " ", "&#x2013;": "--"}

def clean(text):
    text = TAGS.sub("", text)
    for a, b in ENTS.items():
        text = text.replace(a, b)
    for a, b in CHARS.items():
        text = text.replace(a, b)
    return text

def fill_missing_journal(text):
    """BibTeX warns on @article with no journal; arXiv-only entries hit this."""
    out, n = [], 0
    for entry in re.split(r"(?=@\w+\{)", text):
        if entry.startswith("@article") and not re.search(r"\bjournal\s*=", entry, re.I):
            m = re.search(r"arxiv\.org/abs/([\w.\-/]+)", entry, re.I) or \
                re.search(r"ARXIV\.([\w.\-/]+)", entry)
            if m:
                entry = re.sub(r"(@article\{[^,]+,\n)",
                               r"\1  journal = {arXiv preprint arXiv:%s},\n" % m.group(1),
                               entry, count=1)
                n += 1
        out.append(entry)
    return "".join(out), n

def main():
    total = 0
    for name in FILES:
        p = os.path.join(ROOT, "latex", name)
        if not os.path.exists(p):
            print(f"  skip {name} (absent)"); continue
        src = open(p, encoding="utf-8").read()
        dst = clean(src)
        dst, nj = fill_missing_journal(dst)
        left = sorted({c for c in dst if ord(c) > 127})
        if dst != src:
            open(p, "w", encoding="utf-8").write(dst)
        changed = sum(1 for a, b in zip(src, dst) if a != b) or (len(src) != len(dst))
        print(f"  {name}: {'rewritten' if dst != src else 'unchanged'}"
              f"{f', {nj} journal field(s) filled' if nj else ''}")
        if left:
            print(f"    !! {len(left)} unmapped non-ASCII remain: "
                  + " ".join(f"{c!r}(U+{ord(c):04X})" for c in left))
            total += len(left)
    print("clean" if not total else f"{total} character(s) still need a mapping in CHARS")
    return 1 if total else 0

if __name__ == "__main__":
    sys.exit(main())
