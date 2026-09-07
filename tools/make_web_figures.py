#!/usr/bin/env python3
"""Web derivatives of the reproduced figures in latex/fig/.

The manuscript wants print resolution; the page wants to load. Same images,
downscaled once here and committed, so building the page needs no image library
and index.html does not grow by four megabytes of base64.

Print originals live in latex/fig/ and are what Overleaf compiles; these are
copies. Both are covered by latex/fig/CREDITS.md.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "latex", "fig")
DST = os.path.join(ROOT, "site", "fig")
WIDTH = 1100

def main():
    os.makedirs(DST, exist_ok=True)
    for name in sorted(os.listdir(SRC)):
        if not name.lower().endswith((".png", ".jpg")):
            continue
        im = Image.open(os.path.join(SRC, name)).convert("RGB")
        if im.width > WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        out = os.path.join(DST, os.path.splitext(name)[0] + ".jpg")
        im.save(out, quality=82, optimize=True, progressive=True)
        print(f"{name:24s} -> {os.path.basename(out):24s} {im.width}x{im.height}  "
              f"{os.path.getsize(out)//1024} KB")

if __name__ == "__main__":
    main()
