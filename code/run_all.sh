#!/usr/bin/env bash
# Capture BOTH pairs at once. openai_nano and gemini_flash are different providers
# with independent rate limits, so their tracks run in parallel. Within a track the
# two versions run sequentially (same provider -> one shared RPM budget). Analysis
# is done sequentially at the end (it is fast, $0, and writes shared output files).
#
#   ./code/run_all.sh                 # full grid, real
#   SUBGRID=pilot ./code/run_all.sh   # smaller grid
#   CONC=48 ./code/run_all.sh         # more workers per track
#   PILOT_MOCK=1 SUBGRID=pilot ./code/run_all.sh   # offline dry run of the whole thing

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SUBGRID="${SUBGRID:-full}"
CONC="${CONC:-32}"
PAIRS=(openai_nano gemini_flash)
mkdir -p logs
export PILOT_MOCK="${PILOT_MOCK:-0}"
export PYTHONUNBUFFERED=1
PY="${PY:-python3}"

if [ "$PILOT_MOCK" != "1" ]; then
  DOC_KIND=$($PY -c "import sys;sys.path.insert(0,'code/config');import taskcfg;print(taskcfg.DOC_KIND)")
  if [ "$DOC_KIND" = "fundamentals" ]; then
    echo "[run_all] building fundamentals docs (docs/) ..."
    $PY code/capture/build_docs.py --subgrid "$SUBGRID" || { echo "[run_all] build_docs FAILED"; exit 2; }
  else
    echo "[run_all] building no-lookahead price context (inputs/) ..."
    $PY code/capture/build_inputs.py --subgrid "$SUBGRID" || { echo "[run_all] build_inputs FAILED"; exit 2; }
  fi
fi

capture_track () {
  local pair="$1" rc=0
  $PY code/capture/orchestrator.py --pair "$pair" --version v_old --subgrid "$SUBGRID" --concurrency "$CONC" || rc=$?
  $PY code/capture/orchestrator.py --pair "$pair" --version v_new --subgrid "$SUBGRID" --concurrency "$CONC" || rc=$?
  return $rc   # nonzero if EITHER version was incomplete (e.g. daily-quota deferrals)
}

echo "[run_all] capturing ${PAIRS[*]} in parallel (subgrid=$SUBGRID, conc=$CONC). Live logs in logs/."
declare -a PIDS
for pair in "${PAIRS[@]}"; do
  capture_track "$pair" >"logs/${pair}.log" 2>&1 &
  PIDS+=($!)
  echo "  -> $pair track PID $! -> logs/${pair}.log"
done

# live percent heartbeat to this terminal (reads flushed CSV counts)
( while true; do sleep 20; echo "  $(date +%H:%M:%S) $($PY code/status.py --subgrid "$SUBGRID" 2>/dev/null | tail -1)"; done ) &
MON=$!

fail=0
for i in "${!PAIRS[@]}"; do
  if wait "${PIDS[$i]}"; then
    echo "[run_all] ${PAIRS[$i]} capture DONE ($(grep -c ', spend' logs/${PAIRS[$i]}.log 2>/dev/null) versions)"
  else
    echo "[run_all] ${PAIRS[$i]} capture FAILED — see logs/${PAIRS[$i]}.log"; fail=1
  fi
done
kill "$MON" 2>/dev/null || true
[ "$fail" = 1 ] && { echo "[run_all] a capture track failed; not analyzing."; exit 1; }

for pair in "${PAIRS[@]}"; do
  $PY code/capture/freeze.py --pair "$pair" --version v_old
  $PY code/capture/freeze.py --pair "$pair" --version v_new
  $PY code/analysis/run.py --pair "$pair"
  $PY code/render/report.py
  $PY code/render/check_claims.py || echo "[run_all] check failed for $pair"
  mkdir -p results
  cp results/claims.json "results/claims_${pair}.json"
  cp results/PILOT_RESULTS.md "results/results_${pair}.md"
  echo "[run_all] $pair -> results/results_${pair}.md / results/claims_${pair}.json"
done
echo "[run_all] ALL DONE."
