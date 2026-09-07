#!/usr/bin/env python3
"""Static checks for main.tex, standing in for a compiler we do not have here.

Catches the failure modes that actually occur in hand-written IEEE tables:
a row whose cell count disagrees with the column spec, an unclosed
environment, unbalanced braces, and stray non-ASCII that pdflatex will
reject under T1/inputenc. Not a substitute for a real build, but it turns
"probably compiles" into a list of specific things checked.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "latex", "main.tex")

def spec_columns(spec):
    """Count columns in a tabular preamble like {llccp{3cm}}."""
    n, i = 0, 0
    while i < len(spec):
        c = spec[i]
        if c in "lcrX":
            n += 1
        elif c in "pmb" and i + 1 < len(spec) and spec[i + 1] == "{":
            n += 1
            d = 0
            while i < len(spec):
                if spec[i] == "{": d += 1
                elif spec[i] == "}":
                    d -= 1
                    if d == 0: break
                i += 1
        elif c in "@!><" and i + 1 < len(spec) and spec[i + 1] == "{":
            d = 0
            while i < len(spec):
                if spec[i] == "{": d += 1
                elif spec[i] == "}":
                    d -= 1
                    if d == 0: break
                i += 1
        i += 1
    return n

def row_cells(line):
    """Count cells: split on & that is not escaped, ignoring braced groups."""
    n, d, i = 1, 0, 0
    while i < len(line):
        c = line[i]
        if c == "\\": i += 2; continue
        if c == "{": d += 1
        elif c == "}": d -= 1
        elif c == "&" and d == 0: n += 1
        i += 1
    return n

def main():
    text = open(SRC, encoding="utf-8").read()
    lines = text.split("\n")
    errs, warns = [], []

    # 1. non-ASCII outside comments
    for i, l in enumerate(lines, 1):
        code = l.split("%")[0] if not l.lstrip().startswith("%") else ""
        for ch in code:
            if ord(ch) > 127:
                errs.append(f"line {i}: non-ASCII {ch!r} (U+{ord(ch):04X}) in code")

    # 2. brace balance
    d = 0
    for i, l in enumerate(lines, 1):
        code = re.sub(r"(?<!\\)%.*$", "", l)
        code = re.sub(r"\\[{}]", "", code)
        d += code.count("{") - code.count("}")
    if d: errs.append(f"brace imbalance over whole file: {d:+d}")

    # 3. environments
    stack = []
    for i, l in enumerate(lines, 1):
        for m in re.finditer(r"\\begin\{(\w+\*?)\}", l): stack.append((m.group(1), i))
        for m in re.finditer(r"\\end\{(\w+\*?)\}", l):
            if not stack: errs.append(f"line {i}: \\end{{{m.group(1)}}} with no open environment")
            else:
                name, ln = stack.pop()
                if name != m.group(1):
                    errs.append(f"line {i}: \\end{{{m.group(1)}}} closes \\begin{{{name}}} from line {ln}")
    for name, ln in stack: errs.append(f"line {ln}: \\begin{{{name}}} never closed")

    # 4. tabular row widths
    i = 0
    while i < len(lines):
        m = re.search(r"\\begin\{tabular\}\{", lines[i])
        if m:
            # brace-match the column spec: p{3cm} nests, so a regex cannot do this
            s, d, k = m.end(), 1, m.end()
            while k < len(lines[i]) and d:
                if lines[i][k] == "{": d += 1
                elif lines[i][k] == "}": d -= 1
                k += 1
            ncol, start = spec_columns(lines[i][s:k - 1]), i
            j, buf = i + 1, ""
            while j < len(lines) and "\\end{tabular}" not in lines[j]:
                buf += " " + lines[j]
                if "\\\\" in lines[j]:
                    row = buf.split("\\\\")[0]
                    bare = re.sub(r"(?<!\\)%.*$", "", row).strip()
                    if bare and not re.match(r"^\s*\\(toprule|midrule|bottomrule|cmidrule|hline|addlinespace)", bare):
                        if "\\multicolumn" not in bare:
                            n = row_cells(row)
                            if n != ncol:
                                errs.append(f"line {j}: table at line {start+1} declares {ncol} columns, row has {n}")
                    buf = "\\\\".join(buf.split("\\\\")[1:])
                j += 1
            i = j
        i += 1

    # 5. undefined-looking generated macros
    defined = set(re.findall(r"\\newcommand\{\\(\w+)\}",
                             open(os.path.join(ROOT, "latex", "numbers.tex"), encoding="utf-8").read()))
    used = set(re.findall(r"\\((?:Corpus|Scr|Recall|Seed|Set|Src|Read|Harvest|Failed)\w+)", text))
    for u in sorted(used - defined):
        errs.append(f"macro \\{u} used but not defined in numbers.tex")

    # 6. inputs exist
    for inc in re.findall(r"\\input\{([^}]+)\}", text):
        f = os.path.join(ROOT, "latex", inc if inc.endswith(".tex") else inc + ".tex")
        if not os.path.exists(f): errs.append(f"\\input{{{inc}}} -> missing {f}")

    # 7. labels / refs
    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    for r in sorted(set(re.findall(r"\\ref\{([^}]+)\}", text))):
        if r not in labels: errs.append(f"\\ref{{{r}}} has no matching \\label")
    dup = [l for l in labels if text.count("\\label{%s}" % l) > 1]
    for l in dup: errs.append(f"duplicate \\label{{{l}}}")

    print(f"checked {len(lines)} lines, {len(labels)} labels, "
          f"{len(re.findall(r'\\begin.tabular', text))} tables")
    for w in warns: print("WARN ", w)
    for e in errs: print("ERROR", e)
    print(("FAIL: %d problem(s)" % len(errs)) if errs else "OK: no structural problems found")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())
