#!/usr/bin/env python3
"""Verify every citation key in main.tex resolves in refs.bib or refs_context.bib.

A survey that cites a key BibTeX cannot find silently prints "[?]" and the
claim loses its source. This checks mechanically, and for each unresolved key
suggests the closest valid one so a typo is obvious rather than buried.
Exit status is non-zero when anything is unresolved, so refresh.sh can gate on it.
"""
import difflib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEX = os.path.join(ROOT, "latex")

def keys(*names):
    k = set()
    for n in names:
        p = os.path.join(LATEX, n)
        if not os.path.exists(p):
            print(f"!! missing bib file: {n}"); continue
        k |= set(re.findall(r"^@\w+\{([^,\s]+)", open(p, encoding="utf-8").read(), re.M))
    return k

def main():
    valid = keys("refs.bib", "refs_context.bib")
    tex = open(os.path.join(LATEX, "main.tex"), encoding="utf-8").read()
    used = []
    for m in re.finditer(r"\\cite\{([^}]*)\}", tex):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                used.append((k, tex[:m.start()].count("\n") + 1))
    bad = [(k, ln) for k, ln in used if k not in valid]
    uniq = sorted({k for k, _ in used})
    print(f"{len(used)} citations, {len(uniq)} unique keys, {len(valid)} available")
    if bad:
        print(f"\n{len(bad)} UNRESOLVED:")
        for k, ln in bad:
            near = difflib.get_close_matches(k, valid, n=1, cutoff=0.55)
            print(f"  line {ln:>5}  {k:<28} -> {near[0] if near else '(no close match)'}")
    uncited = sorted(valid - set(uniq))
    print(f"\n{len(uncited)} bib entries not cited in the prose:")
    for k in uncited:
        print("   ", k)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
