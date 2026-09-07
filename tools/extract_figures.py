#!/usr/bin/env python3
"""Crop figures out of the reusable PDFs, anchored on their captions.

There is no figure object in a PDF -- there is ink, and somewhere under it a
line that starts "Figure 3:". So the caption is the anchor: find it in the text
layer, decide which column it sits in, and take the rectangle above it that
reaches up to the previous line of text in that same column. Render the page and
cut that rectangle out.

Only papers that `fetch_licenses.py` marked `reusable` are touched; everything
else is skipped by name, so a restricted figure cannot reach the manuscript by
accident.

    python3 tools/extract_figures.py            # every reusable paper, figures 1-3
    python3 tools/extract_figures.py 2303.03480 # one paper, all its figures
"""
import json, os, re, subprocess, sys, xml.etree.ElementTree as ET
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "data", "pdf")
OUT = os.path.join(ROOT, "data", "figures")
LIC = os.path.join(ROOT, "data", "arxiv_licenses.json")
DPI = 260
CAP = re.compile(r"^(Figure|Fig\.?)\s*(\d+)", re.I)
NS = {"x": "http://www.w3.org/1999/xhtml"}

def pages(pdf):
    """-bbox-layout groups the words into lines; plain -bbox emits words only."""
    xml = subprocess.run(["pdftotext", "-bbox-layout", "-q", pdf, "-"],
                         capture_output=True, text=True, timeout=180).stdout
    # ligatures and glyphs with no Unicode mapping come out as control characters,
    # which are not legal XML -- half the corpus fails to parse without this
    xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", xml)
    root = ET.fromstring(xml)
    for pno, page in enumerate(root.iter("{http://www.w3.org/1999/xhtml}page"), 1):
        w, h = float(page.get("width")), float(page.get("height"))
        lines = []
        for ln in page.iter("{http://www.w3.org/1999/xhtml}line"):
            words = [(float(x.get("xMin")), float(x.get("yMin")), float(x.get("xMax")),
                      float(x.get("yMax")), (x.text or "")) for x in ln]
            if words:
                lines.append({"x0": min(w0[0] for w0 in words), "y0": min(w0[1] for w0 in words),
                              "x1": max(w0[2] for w0 in words), "y1": max(w0[3] for w0 in words),
                              "text": " ".join(w0[4] for w0 in words)})
        yield pno, w, h, sorted(lines, key=lambda l: (l["y0"], l["x0"]))

def column(line, w):
    """Two-column papers: a caption is left, right, or spans both (a figure*)."""
    mid = w / 2
    if line["x1"] < mid + 12:
        return 0.06 * w, mid - 0.01 * w
    if line["x0"] > mid - 12:
        return mid + 0.01 * w, 0.94 * w
    return 0.06 * w, 0.94 * w

def trim(im, tol=6):
    """Drop the white margin the crop inevitably includes."""
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im.convert("RGB"), bg).convert("L").point(lambda p: p > tol and 255)
    bb = diff.getbbox()
    return im.crop((max(0, bb[0] - 6), max(0, bb[1] - 6),
                    min(im.width, bb[2] + 6), min(im.height, bb[3] + 6))) if bb else im

def extract(aid, want=(1, 2, 3)):
    pdf = os.path.join(PDF, aid + ".pdf")
    made = []
    for pno, w, h, lines in pages(pdf):
        for i, ln in enumerate(lines):
            m = CAP.match(ln["text"].strip())
            if not m or int(m.group(2)) not in want:
                continue
            x0, x1 = column(ln, w)
            top = 0.05 * h
            for prev in lines[:i]:                   # the nearest text above, same column
                if prev["y1"] < ln["y0"] - 4 and prev["x1"] > x0 and prev["x0"] < x1:
                    top = max(top, prev["y1"] + 5)
            if ln["y0"] - top < 55:                  # too thin to be a figure: a wrapped caption
                continue
            png = f"/tmp/pg-{aid}-{pno}.png"
            if not os.path.exists(png):
                subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(pno), "-l", str(pno),
                                "-png", "-singlefile", pdf, png[:-4]], check=True, timeout=180)
            s = DPI / 72.0
            im = Image.open(png).crop((int(x0 * s), int(top * s), int(x1 * s), int(ln["y0"] * s)))
            if im.width < 120 or im.height < 90:
                continue
            out = os.path.join(OUT, f"{aid}-fig{m.group(2)}.png")
            im = trim(im)
            im.save(out)
            made.append((out, m.group(0), ln["text"][:110], im.size))
    return made

def main():
    os.makedirs(OUT, exist_ok=True)
    lic = json.load(open(LIC, encoding="utf-8"))
    ids = sys.argv[1:] or [k for k, v in sorted(lic.items()) if v["verdict"] == "reusable"]
    for aid in ids:
        if lic.get(aid, {}).get("verdict") != "reusable":
            print(f"{aid}: skipped -- {lic.get(aid, {}).get('licence', 'unknown licence')}")
            continue
        try:
            for out, cap, text, size in extract(aid):
                print(f"{os.path.basename(out):28s} {size[0]}x{size[1]:<5d} {text}")
        except Exception as e:
            print(f"{aid}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    sys.exit(main())
