#!/usr/bin/env bash
# Temperature-sensitivity robustness for one pair. Captures the tempsweep subgrid
# (8x3) at T in {0.0, 0.7, 1.0} into tagged CSVs, then analyzes the excess flip rate
# at each temperature. Needs inputs/ already built (make -C code inputs SUBGRID=full).
#   PAIR=openai_nano ./code/run_tempsweep.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PAIR="${PAIR:-openai_nano}"
CONC="${CONC:-16}"
export PYTHONUNBUFFERED=1
PY="${PY:-python3}"

for T in 0.0 0.7 1.0; do
  tag="_T$(echo "$T" | tr -d '.')"
  echo "[tempsweep] $PAIR at T=$T (tag $tag)"
  for V in v_old v_new; do
    if $PY code/capture/orchestrator.py --pair "$PAIR" --version "$V" --subgrid tempsweep --temperature "$T" --tag "$tag" --concurrency "$CONC"; then
      $PY code/capture/freeze.py --pair "$PAIR" --version "$V" --tag "$tag"
    else
      echo "[tempsweep] $PAIR $V T=$T INCOMPLETE (quota/failures) — left writable for backfill, not frozen."
    fi
  done
done
$PY code/analysis/tempsweep.py --pair "$PAIR"
