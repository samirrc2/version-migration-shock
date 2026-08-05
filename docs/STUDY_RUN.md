# Run sequence — Version Migration as a Correlated Shock

Two paths. **Verification (default)** regenerates every number from the frozen data,
needs no keys, and costs nothing. **Collection (optional)** re-runs the 14,400 live
model calls and requires API keys on your machine (the sandbox cannot reach provider
APIs). Do not skip the pre-registration freeze if re-collecting.

## A. Verify from frozen data (keys-free, $0)

```bash
cd "/Users/samirchincholikar/Desktop/NIW/Paper 2"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

bash code/reproduce.sh            # analyze both pairs + gate-check
bash code/reproduce.sh --verify   # determinism: analyze each pair twice, hash-compare
```

Outputs: `results/claims_<pair>.json`, `results/results_<pair>.md`. The gate (`code/render/check_claims.py`)
fails if any reported number disagrees with the frozen analysis.

## B. Re-collect the dataset (optional; needs keys; costed)

Keys expected at `../API Keys/keys.env.txt` (OPENAI_API_KEY, GEMINI_API_KEY, FMP_API_KEY).

```bash
python3 capture/secrets.py            # confirm keys FOUND

# Ground-truth inputs (no model cost): reported financials + Altman labels
make docs SUBGRID=full                # FMP fundamentals -> docs/
make outcomes SUBGRID=full            # Altman Z'' bands -> data/outcomes/ground_truth.json

# PHASE 0 — pre-registration freeze BEFORE any model call (already frozen for the
# confirmatory run; only needed for a fresh study). See PREREGISTRATION.md /
# PREREGISTRATION.freeze.txt.

# PHASE 1 — capture both migrations in parallel (per-provider rate limits)
make all SUBGRID=full CONC=32         # capture -> freeze -> analyze -> render -> check
python3 status.py --subgrid full      # live percent progress

# PHASE 2 — robustness
make tempsweep PAIR=openai_nano
make tempsweep PAIR=gemini_flash
```

`data/raw/*.csv` are frozen read-only after collection; SHA-256 receipts are written to
`data/frozen/` and aggregated in `DATA_MANIFEST.md`. Do not regenerate a frozen file —
a correction requires a new versioned CSV plus a manifest changelog entry.

## Offline dry run (no keys, mocked responses)

```bash
PILOT_MOCK=1 SUBGRID=pilot ./run_all.sh
```
