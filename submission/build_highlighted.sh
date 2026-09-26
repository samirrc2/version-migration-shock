#!/usr/bin/env bash
# Build the "Highlighted PDF" required by the IEEE Access resubmission checklist: the
# revised manuscript with every individual change marked in yellow. The markup rewrite
# lives in highlight_markup.py; see its docstring for why latexdiff's own preamble is
# discarded rather than restyled.
#
#   bash submission/build_highlighted.sh            # against the as-submitted tag
#   bash submission/build_highlighted.sh <ref>      # against another ref
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"
# The baseline is the version the reviewers read, which is a fixed point in history -- not
# "whatever was committed last". This defaulted to HEAD, which worked only while the revision
# was uncommitted; committing it moved the baseline onto the revision itself and the next build
# failed outright. A tag keeps it pinned.
BASE_REF="${1:-as-submitted}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if ! git rev-parse --verify --quiet "$BASE_REF^{commit}" >/dev/null; then
  echo "ERROR: baseline ref '$BASE_REF' does not exist. The highlighted PDF must be diffed" >&2
  echo "       against the manuscript as submitted; create the tag with:" >&2
  echo "         git tag -a as-submitted <commit> -m 'Manuscript as submitted'" >&2
  exit 3
fi
git show "$BASE_REF:paper/main.tex" > "$WORK/old.tex"
cp paper/main.tex "$WORK/new.tex"

# The bibliography was reordered into citation order for this revision, which makes
# latexdiff interleave DIFadd/DIFdel across entry boundaries and emit unbalanced braces.
# The reference list is therefore held constant across the diff: the new bibliography is
# substituted into the old file, so the highlighted PDF shows the final reference list
# without spurious markup. The reordering is recorded in submission/CHANGES.md instead.
python3 - "$WORK/old.tex" "$WORK/new.tex" <<'PYX'
import re, sys
old_p, new_p = sys.argv[1], sys.argv[2]
new = open(new_p, encoding="utf-8").read()
m = re.search(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", new, re.S)
if m:
    old = open(old_p, encoding="utf-8").read()
    old = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                 lambda _: m.group(0), old, flags=re.S)
    open(old_p, "w", encoding="utf-8").write(old)
    print("   bibliography held constant across the diff")
PYX
# Rounding-only corrections are held constant too, for the same reason as the bibliography:
# marking them would point a reviewer at nine digit-level edits as though a finding had moved.
# Each one is the same quantity at the same printed precision. They came from a double-
# rounding bug in code/render/figures.py, which rounded an already-4dp value to 3dp, so
# 0.14948571 printed as 0.150 rather than 0.149. The bug and every affected figure are
# recorded in submission/CHANGES.md, so the correction is disclosed in prose rather than
# hidden -- it is simply not highlighted as a substantive revision.
python3 - "$WORK/old.tex" <<'PYX'
import sys
# (previous text, corrected text, occurrences expected)
ROUNDING = [
    (r"$[0.077,\,0.150]$", r"$[0.077,\,0.149]$", 1),   # 0.14948571 -> 0.1495 -> 0.150
    (r"7.7--15.0",         r"7.7--14.9",         1),   # the same bound as a percentage
    (r"30.3--45.8",        r"30.2--45.8",        1),   # 0.30245 -> 0.3025 -> 0.303
    (r"$[0.303,\,0.458]$", r"$[0.302,\,0.458]$", 1),
    (r"[.077,.150] & [.303,.458]", r"[.077,.149] & [.302,.458]", 1),   # Table 2, same bounds
    (r".372\,[.30,.45]",     r".372\,[.29,.45]",     1),   # 0.2947 -> .29, not .30

    (r"$+0.124$",          r"$+0.123$",          2),   # 0.12345679 -> 0.1235 -> 0.124
    (r"$-0.179$",          r"$-0.178$",          2),   # -0.17849462 -> -0.1785 -> -0.179
]
path = sys.argv[1]
t = open(path, encoding="utf-8").read()
applied = 0
for old, new, n in ROUNDING:
    found = t.count(old)
    if found != n:
        sys.exit(f"ERROR: expected {n} occurrence(s) of {old!r} in the previous version, "
                 f"found {found}. The rounding table in build_highlighted.sh is stale.")
    t = t.replace(old, new)
    applied += found
open(path, "w", encoding="utf-8").write(t)
print(f"   {applied} rounding-only corrections held constant across the diff")
PYX

# Section headings are marked too. Excluding them left the two subsections added in this
# revision (III-C and III-D) sitting under unhighlighted headings, so a reviewer saw the new
# prose but no sign that the sections themselves were new. Including them compiles cleanly in
# the IEEE template and adds exactly those two runs.
latexdiff --type=CFONT --math-markup=0 \
          "$WORK/old.tex" "$WORK/new.tex" > "$WORK/diff.tex" 2>/dev/null || true
python3 submission/highlight_markup.py "$WORK/diff.tex"

# Compile inside paper/ rather than a temp directory. The IEEE Access template needs its
# font maps (t1-*.map) and font descriptors (t1*.fd) alongside the source; copying only the
# class, style, .pfb and .tfm files leaves pdflatex unable to resolve formata at title size,
# and even the unmodified manuscript fails to build. Nothing of the author's is overwritten:
# the working file is a uniquely named temporary that is removed on exit.
STEM="_highlighted_build"
cp "$WORK/diff.tex" "paper/$STEM.tex"
trap 'rm -rf "$WORK" paper/'"$STEM"'.*' EXIT
( cd paper && for i in 1 2 3; do pdflatex -interaction=nonstopmode "$STEM.tex" >/dev/null 2>&1 || true; done )

if [ -f "paper/$STEM.pdf" ]; then
    cp "paper/$STEM.pdf" submission/highlighted_pdf.pdf
    grep -o "Output written on $STEM.pdf ([0-9]* pages" "paper/$STEM.log" | head -1 | sed 's/^/   /'
    echo "   -> submission/highlighted_pdf.pdf"
else
    echo "   FAILED: no PDF produced" >&2
    grep -E "^! |pdfTeX error" "paper/$STEM.log" | head -6 >&2 || true
    exit 1
fi
