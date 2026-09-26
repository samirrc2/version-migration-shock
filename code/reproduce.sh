#!/usr/bin/env bash
# Top-level reproduction entry point (IEEE Access / Code Ocean).
#
# Default path is KEYS-FREE and $0: it regenerates every reported number and the
# results tables for both migrations from the frozen capture CSVs in data/raw/,
# then runs the build gate that fails if any number disagrees with the frozen
# analysis. Outputs go under results/ only. Re-collecting the 14,400 model calls
# is optional, costs money, needs API keys, and is NOT required to verify claims.
#
#   bash code/reproduce.sh              # analyze both pairs + gate-check (default)
#   bash code/reproduce.sh --verify     # analyze each pair TWICE and hash-compare
#   bash code/reproduce.sh --help
#
# Must run from the repository root (or any cwd — this script cds to ROOT).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PY:-python3}"
PAIRS=(openai_nano gemini_flash)
RES=results
mkdir -p "$RES"

sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
usage() { sed -n '2,14p' "$0"; exit 0; }
MODE="run"
case "${1:-}" in
  --help|-h) usage ;;
  --verify)  MODE="verify" ;;
  "")        ;;
  *) echo "unknown option: $1" >&2; exit 2 ;;
esac

for p in "${PAIRS[@]}"; do
  if [[ ! -f "data/raw/runs_${p}_v_old.csv" || ! -f "data/raw/runs_${p}_v_new.csv" ]]; then
    echo "ERROR: frozen data for '${p}' missing under data/raw/ (see DATA_MANIFEST.md)." >&2
    exit 1
  fi
done

analyze_pair() {
  local p="$1"
  $PY code/analysis/run.py --pair "$p" >/dev/null
  cp "$RES/claims.json" "$RES/claims_${p}.json"
  $PY code/render/report.py >/dev/null
  cp "$RES/PILOT_RESULTS.md" "$RES/results_${p}.md"
}

if [[ "$MODE" == "verify" ]]; then
  echo "[reproduce] determinism check: analyzing each pair under three hash seeds and hash-comparing"
  # Two plain re-runs only catch order-dependence if the interpreter happens to pick hash seeds
  # whose effect differs, which makes the test probabilistic. Iterating a set of string keys is
  # the usual way this creeps in: the sum order changes and the last bits of a float move. The
  # seeds are therefore pinned to values known to differ, so the check either catches it or the
  # code really is order-independent.
  ok=1
  for p in "${PAIRS[@]}"; do
    hs=()
    for seed in 0 1 12345; do
      PYTHONHASHSEED=$seed $PY code/analysis/run.py --pair "$p" >/dev/null
      hs+=("$(sha256 "$RES/claims.json")")
    done
    if [[ "${hs[0]}" == "${hs[1]}" && "${hs[1]}" == "${hs[2]}" ]]; then
      echo "  $p: IDENTICAL  ${hs[0]:0:16}"
    else
      echo "  $p: MISMATCH across hash seeds (${hs[0]:0:12} / ${hs[1]:0:12} / ${hs[2]:0:12})"
      ok=0
    fi
  done
  [[ "$ok" == 1 ]] && echo "[reproduce] deterministic: byte-identical across re-runs" || { echo "[reproduce] NON-DETERMINISTIC"; exit 1; }
  exit 0
fi

echo "[reproduce] regenerating results/ from frozen data/ (keys-free, \$0)"
for p in "${PAIRS[@]}"; do
  echo "  -> $p"
  analyze_pair "$p"
  # The temperature robustness reads the frozen T-tagged captures, so it is keys-free and belongs
  # in the default path. Without it a fresh clone has no tempsweep_<pair>.json and the manuscript
  # gate cannot resolve the Table 4 figures, which is how the clean-room run first failed.
  $PY code/analysis/tempsweep.py --pair "$p" >/dev/null 2>&1 ||       echo "     [$p] tempsweep skipped (T-subgrid captures absent)"
  $PY code/render/check_claims.py | sed "s/^/     [$p] /"
done
# The per-pair gate defers the manuscript check until every pair's claims file exists, so it
# runs once more here. On a fresh clone this is the invocation that actually gates main.tex.
echo "[reproduce] manuscript number check (all pairs present)"
$PY code/render/check_claims.py

# check_claims.py only reads paper/main.tex. The README, the response letter, Table 2 cell by
# cell and the guidance citations were checked by scripts a clean run never invoked, so a stale
# figure in any of them survived a full reproduction. Run them here, where the results exist.
echo "[reproduce] documentation and response-letter check"
# Exit 2 means the manuscript, README and letter are not published in this copy -- the /code +
# /data capsule layout. That is "not checkable here", not a pass and not a failure.
rc=0; $PY code/render/check_docs.py || rc=$?
if [[ "$rc" == 2 ]]; then
  # Absent because this is a /code + /data capsule, where they are never mounted, or absent
  # because someone deleted them from a full checkout? The first is the documented layout and
  # is a clean run; the second is a copy that cannot be fully verified and must say so.
  if [[ -d paper && -d submission ]]; then DOCS_INCOMPLETE=1; fi
elif [[ "$rc" != 0 ]]; then
  exit "$rc"
fi

# The highlighted PDF is only trustworthy if the revision rebuilds exactly from the markup. That
# needs a built diff; skip rather than fail when the package has not been assembled (exit 2 is
# "could not check here", which is not a pass).
if [[ -f submission/_highlighted_build.tex || -f submission/highlighted_pdf.pdf ]]; then
  echo "[reproduce] highlighting round-trip"
  rc=0; $PY submission/check_highlighting.py || rc=$?
  if [[ "$rc" == 2 ]]; then
    DOCS_INCOMPLETE=1
  elif [[ "$rc" != 0 ]]; then
    exit "$rc"
  fi
elif [[ -d submission ]]; then
  echo "[reproduce] highlighting round-trip SKIPPED: run bash submission/build_submission.sh first"
  DOCS_INCOMPLETE=1
fi

echo "[reproduce] done. Outputs in $RES/claims_<pair>.json and $RES/results_<pair>.md"
echo "[reproduce] optional live re-collection (needs API keys, ~costed): make -C code all SUBGRID=full"

# Exit 2 means "a gate that applies to this copy could not run", which must not read as a pass.
# A capsule (/code + /data only) has no document gates to run, so it exits 0.
if [[ "${DOCS_INCOMPLETE:-0}" == 1 ]]; then
  echo "[reproduce] INCOMPLETE: the analysis reproduced, but a document gate could not run"
  exit 2
fi
exit 0
