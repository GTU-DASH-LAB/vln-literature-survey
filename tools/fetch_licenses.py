#!/usr/bin/env python3
"""Ask arXiv, per paper, whether its figures may be reproduced.

A survey that reprints a figure needs the right to reprint it. arXiv's *default*
licence is a non-exclusive licence to distribute **the paper**, which grants no
one the right to lift a figure out of it; only the Creative Commons options do.
The Atom API does not carry the licence field, so this goes to OAI-PMH, which
does, and writes one verdict per arXiv id:

    reusable   CC-BY, CC-BY-SA, CC0 -- reproducible with attribution
    restricted CC-BY-NC-* , CC-BY-ND-*  -- attribution is not enough
    no-reuse   arXiv's own licence, or none recorded

Only `reusable` may be reproduced, and every reproduction still carries the
licence in its caption. Resumable: already-known ids are never re-fetched.
"""
import json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "data", "pdf")
OUT = os.path.join(ROOT, "data", "arxiv_licenses.json")
OAI = "https://oaipmh.arxiv.org/oai?verb=GetRecord&identifier=oai:arXiv.org:{}&metadataPrefix=arXiv"

CLASS = [
    (r"creativecommons\.org/publicdomain/zero", "reusable",   "CC0 1.0"),
    (r"creativecommons\.org/licenses/by/4\.0",  "reusable",   "CC BY 4.0"),
    (r"creativecommons\.org/licenses/by-sa/4\.0", "reusable", "CC BY-SA 4.0"),
    (r"creativecommons\.org/licenses/by-nc-sa", "restricted", "CC BY-NC-SA"),
    (r"creativecommons\.org/licenses/by-nc-nd", "restricted", "CC BY-NC-ND"),
    (r"creativecommons\.org/licenses/by-nc",    "restricted", "CC BY-NC"),
    (r"creativecommons\.org/licenses/by-nd",    "restricted", "CC BY-ND"),
    (r"arxiv\.org/licenses/nonexclusive-distrib", "no-reuse", "arXiv non-exclusive"),
]

def classify(url):
    for pat, verdict, name in CLASS:
        if re.search(pat, url or ""):
            return verdict, name
    return ("no-reuse", "none recorded") if not url else ("no-reuse", url)

def get(aid, tries=4):
    """OAI-PMH answers 503 with Retry-After when it wants you to slow down."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(OAI.format(aid), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 503:
                time.sleep(int(e.headers.get("Retry-After", 20)))
                continue
            return f"__http_{e.code}__"
        except Exception as e:                       # network flake: back off and retry
            time.sleep(5 * (attempt + 1))
    return "__failed__"

def main():
    known = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    ids = sorted(f[:-4] for f in os.listdir(PDF) if f.endswith(".pdf"))
    todo = [i for i in ids if i not in known]
    print(f"{len(ids)} pdfs, {len(known)} already known, {len(todo)} to fetch", flush=True)
    for n, aid in enumerate(todo, 1):
        xml = get(aid)
        m = re.search(r"<license>([^<]*)</license>", xml)
        d = re.search(r"<created>([^<]*)</created>", xml)
        verdict, name = classify(m.group(1) if m else "")
        known[aid] = {"licence_url": m.group(1) if m else None, "licence": name,
                      "verdict": verdict, "created": d.group(1) if d else None}
        print(f"[{n}/{len(todo)}] {aid}  {verdict:10s} {name}", flush=True)
        json.dump(known, open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
        time.sleep(3.2)                              # arXiv asks for one request per 3 s
    tally = {}
    for v in known.values():
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
    print("\n" + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    print(f"-> {os.path.relpath(OUT, ROOT)}")

if __name__ == "__main__":
    sys.exit(main())
