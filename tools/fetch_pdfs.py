#!/usr/bin/env python3
"""Download the open-access PDF of every reading-list paper and extract its text.

Abstracts are enough to place a paper in a taxonomy. They are not enough to fill a
results table -- SR/SPL/NE live in the paper's own tables, and inventing them would
make the survey worthless. This fetches the full text so those numbers can be read.

Only arXiv is used as a source: it is open access, it covers 84 of the 98, and its
rate limit is documented (one request per three seconds, identify yourself). Papers
without an arXiv id are left to be read by hand -- they are listed at the end.

  python3 tools/fetch_pdfs.py            # download + extract
  python3 tools/fetch_pdfs.py --extract  # re-extract from PDFs already on disk

Writes data/pdf/<arxiv>.pdf and data/txt/<arxiv>.txt.
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PDF, TXT = os.path.join(DATA, "pdf"), os.path.join(DATA, "txt")
os.makedirs(PDF, exist_ok=True); os.makedirs(TXT, exist_ok=True)
UA = {"User-Agent": "gtu-vln-survey/1.0 (academic literature survey; contact via repository)"}

notes = json.load(open(os.path.join(DATA, "reading_notes.json"), encoding="utf-8"))["rows"]
want = [r for r in notes if r.get("arxiv")]
print(f"{len(want)} of {len(notes)} have an arXiv id", file=sys.stderr)

if "--extract" not in sys.argv:
    for i, r in enumerate(want, 1):
        dst = os.path.join(PDF, f"{r['arxiv']}.pdf")
        if os.path.exists(dst) and os.path.getsize(dst) > 20000:
            continue
        url = f"https://arxiv.org/pdf/{r['arxiv']}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as rsp:
                blob = rsp.read()
            if blob[:4] != b"%PDF":
                print(f"  [{i:>2}] {r['arxiv']}  NOT A PDF ({len(blob)} B)", file=sys.stderr)
            else:
                open(dst, "wb").write(blob)
                print(f"  [{i:>2}] {r['arxiv']}  {len(blob)/1024:>6.0f} KB  {r['title'][:52]}", file=sys.stderr)
        except urllib.error.HTTPError as e:
            print(f"  [{i:>2}] {r['arxiv']}  HTTP {e.code}", file=sys.stderr)
        except Exception as e:
            print(f"  [{i:>2}] {r['arxiv']}  {type(e).__name__}", file=sys.stderr)
        time.sleep(3.1)          # arXiv asks for one request per three seconds

# ── extract ──────────────────────────────────────────────────────────────────
ok = fail = 0
for r in want:
    src = os.path.join(PDF, f"{r['arxiv']}.pdf")
    dst = os.path.join(TXT, f"{r['arxiv']}.txt")
    if not os.path.exists(src): fail += 1; continue
    if os.path.exists(dst) and os.path.getsize(dst) > 2000: ok += 1; continue
    try:
        subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", src, dst],
                       check=True, capture_output=True, timeout=120)
        ok += 1
    except Exception as e:
        print(f"  extract failed {r['arxiv']}: {type(e).__name__}", file=sys.stderr); fail += 1

missing = [r for r in notes if not r.get("arxiv")]
print(f"\nextracted {ok}, failed/absent {fail}", file=sys.stderr)
print(f"no arXiv id -- read by hand ({len(missing)}):", file=sys.stderr)
for r in missing:
    print(f"    [{r['rank']:>3}] {r['venue'][:34]:<34} {r['title'][:60]}", file=sys.stderr)
