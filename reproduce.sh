#!/usr/bin/env bash
# Top-level reproduction entry point (IEEE Access / Code Ocean).
#
# Default path is KEYS-FREE and $0: it regenerates every reported number and the
# results tables for both migrations from the frozen capture CSVs in data/raw/,
# then runs the build gate that fails if any number disagrees with the frozen
# analysis. Re-collecting the 14,400 model calls is optional, costs money, needs
# API keys, and is NOT required to verify the article's claims.
#
#   bash reproduce.sh              # analyze both pairs + gate-check (default)
#   bash reproduce.sh --verify     # analyze each pair TWICE and hash-compare (determinism)
#   bash reproduce.sh --help
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PY="${PY:-python3}"
PAIRS=(openai_nano gemini_flash)

usage() { sed -n '2,13p' "$0"; exit 0; }
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

analyze_pair() {  # -> writes claims.json, copies to claims_<pair>.json + results_<pair>.md
  local p="$1"
  $PY analysis/run.py --pair "$p" >/dev/null
  cp claims.json "claims_${p}.json"
  $PY render/report.py >/dev/null
  cp PILOT_RESULTS.md "results_${p}.md"
}

if [[ "$MODE" == "verify" ]]; then
  echo "[reproduce] determinism check: analyzing each pair twice and hash-comparing"
  ok=1
  for p in "${PAIRS[@]}"; do
    $PY analysis/run.py --pair "$p" >/dev/null; h1=$(shasum -a 256 claims.json | awk '{print $1}')
    $PY analysis/run.py --pair "$p" >/dev/null; h2=$(shasum -a 256 claims.json | awk '{print $1}')
    if [[ "$h1" == "$h2" ]]; then echo "  $p: IDENTICAL  ${h1:0:16}"; else echo "  $p: MISMATCH ($h1 vs $h2)"; ok=0; fi
  done
  [[ "$ok" == 1 ]] && echo "[reproduce] deterministic: byte-identical across re-runs" || { echo "[reproduce] NON-DETERMINISTIC"; exit 1; }
  exit 0
fi

echo "[reproduce] regenerating results for both migrations from frozen data (keys-free, \$0)"
for p in "${PAIRS[@]}"; do
  echo "  -> $p"
  analyze_pair "$p"
  $PY render/check_claims.py | sed "s/^/     [$p] /"
done
echo "[reproduce] done. Per-pair results in claims_<pair>.json and results_<pair>.md."
echo "[reproduce] optional live re-collection (needs API keys, ~costed): make all SUBGRID=full"
