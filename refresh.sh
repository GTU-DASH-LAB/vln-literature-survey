#!/usr/bin/env bash
# Rebuild everything downstream of the raw log, then the page. Queries nothing.
#
#   ./refresh.sh              rebuild from data/corpus_raw.csv as it stands
#   ./refresh.sh --harvest    harvest every source first, then rebuild
#
# Safe to run at any time: the raw log is append-only, screening keeps human decisions,
# and every number on the page is regenerated from the files rather than typed into them.
set -euo pipefail
cd "$(dirname "$0")"

export SSL_CERT_FILE="${SSL_CERT_FILE:-$(python3 -c 'import certifi;print(certifi.where())')}"

if [[ "${1:-}" == "--harvest" ]]; then
  for src in openalex crossref ieee semantic_scholar arxiv dblp openreview; do
    echo "── harvesting $src"
    python3 tools/harvest.py --only "$src" || echo "   $src failed, continuing"
  done
fi

python3 tools/harvest.py --rebuild   # corpus + PRISMA counts from the raw log
python3 tools/screen.py                # IC/EC pre-screen, human decisions preserved
python3 tools/reading_list.py          # the ~100 papers to read
python3 tools/recall_audit.py          # seed recall, before/after the change
python3 tools/build.py                 # index.html, every number injected
python3 tools/make_latex.py            # latex/numbers.tex — the manuscript's corpus figures
echo "done — open index.html, and recompile latex/main.tex on Overleaf"
