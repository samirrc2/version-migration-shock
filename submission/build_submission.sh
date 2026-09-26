#!/usr/bin/env bash
# Assemble the four files IEEE Access asks for, under the names the covering letter uses.
#
#   bash submission/build_submission.sh            # rebuild all four
#   bash submission/build_submission.sh --check     # report drift, exit 1 if stale
#
# paper/main.tex keeps its name: the claim gate (code/render/check_claims.py) and
# code/reproduce.sh both address it, and renaming the source to match the upload would mean
# editing the reproduction path to suit a submission portal. The journal-facing names live
# here instead, so submission/ is exactly what gets uploaded:
#
#   main_manuscript.pdf                   clean manuscript          ("Main Manuscript")
#   main_manuscript.docx                  Word version of the same
#   highlighted_pdf.pdf                   changes marked in yellow  ("Highlighted PDF")
#   IEEE-Access-Response-to-Reviewers.pdf point-by-point response
#
# main_manuscript.* are copies of paper/main.*, so they can drift. --check compares them.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"

if [ "${1:-}" = "--check" ]; then
    stale=0
    for pair in "paper/main.pdf:submission/main_manuscript.pdf" \
                "paper/main.docx:submission/main_manuscript.docx"; do
        src="${pair%%:*}"; dst="${pair##*:}"
        if [ ! -f "$dst" ]; then
            echo "MISSING: $dst"; stale=1
        elif ! cmp -s "$src" "$dst"; then
            echo "STALE: $dst differs from $src"; stale=1
        fi
    done
    for f in submission/highlighted_pdf.pdf submission/IEEE-Access-Response-to-Reviewers.pdf; do
        [ -f "$f" ] || { echo "MISSING: $f"; stale=1; }
    done
    [ "$stale" = 0 ] && echo "submission package is current" \
                     || echo "run: bash submission/build_submission.sh"
    exit "$stale"
fi

echo "== 1/4 manuscript PDF =="
( cd paper && for i in 1 2 3; do
      pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
      [ "$i" = 1 ] && (bibtex main >/dev/null 2>&1 || true)
  done; grep -o "Output written.*" main.log || true )

echo "== 2/4 Word version =="
python3 render/build_docx.py

echo "== 3/4 upload copies =="
cp paper/main.pdf  submission/main_manuscript.pdf
cp paper/main.docx submission/main_manuscript.docx
echo "   main_manuscript.pdf, main_manuscript.docx <- paper/main.{pdf,docx}"

echo "== 4/4 highlighted + response =="
bash submission/build_highlighted.sh
python3 submission/build_response.py

echo
bash "$ROOT/submission/build_submission.sh" --check
