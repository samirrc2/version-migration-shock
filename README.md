# Version Migration as a Correlated Shock

Reproducible study and artifact for the paper *"Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems."*

We measure the decision discontinuity a **vendor model update** induces in a fixed, deterministic LLM decision pipeline, on a real, objectively-graded financial task (credit-health classification, SAFE / WATCH / DISTRESS, graded against Altman Z'' bands). Two vendor-declared "recommended replacement" migrations are studied:

- **openai_nano**: `gpt-5-nano-2025-08-07` → `gpt-5.4-nano`
- **gemini_flash**: `gemini-2.5-flash` → `gemini-3.5-flash`

**Headline result.** Both migrations produce a large, highly significant shock, but of *opposite character*: the OpenAI update flips 0.112 of assessments above the within-version noise floor (95% CI [0.077, 0.150]) as genuine per-company reconsideration toward DISTRESS; the Gemini update flips 0.381 (95% CI [0.303, 0.458]) as a wholesale distributional shift toward SAFE. Neither improves accuracy against ground truth. The character of a migration shock does not generalize across vendors.

## Design and integrity

- **Pre-registered.** `PREREGISTRATION.md` was frozen (SHA-256 in `PREREGISTRATION.freeze.txt`) *before* any credit-task model call, so both pairs are confirmatory. Post-freeze changes are in `PREREGISTRATION_AMENDMENTS.md`.
- **Version isolation.** A cell-parity seed keyed on `(ticker, date, replicate)` only is identical for both versions at each cell, so the version is the sole difference (zero seed mismatches verified).
- **Primary endpoint.** `excess_flip_rate = cross_version_flip_rate − within_version_flip_rate`, cluster-bootstrapped over companies (seed 42, 2000 draws).
- **Deterministic + gated.** `analysis/run.py` is a pure, seeded function of the frozen data; `render/check_claims.py` fails the build if any manuscript number disagrees with the frozen analysis or a slot is unfilled.

## Repository layout

```
config/     task.yaml, models.yaml, pairs.yaml, grid.yaml, loader/taskcfg    # one schema; task is switchable
capture/    orchestrator.py, agent.py, build_docs/inputs/outcomes.py, freeze.py, secrets.py
analysis/   metrics.py, stats.py, baseline.py, groundtruth.py, outcomes.py, tempsweep.py, run.py
render/     report.py, figures.py, fill_manuscript.py, check_claims.py
paper/      manuscript.md (auto-filling), paper_ieee_access.tex/.pdf, slots.yaml
data/frozen/  per-capture SHA-256 receipts     figures/  generated figures
PREREGISTRATION*.md   DATA_MANIFEST.md   Makefile   run_all.sh   run_tempsweep.sh
```

Raw model-capture CSVs (`data/raw/`) and fetched context (`inputs/`, `docs/`) are **not** committed — they are large and require API access to regenerate. Their SHA-256 hashes are in `DATA_MANIFEST.md` and `data/frozen/*.freeze.json`; the released dataset can be verified byte-for-byte.

## Reproduce

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# API keys expected at ../API Keys/keys.env.txt (OPENAI_API_KEY, GEMINI_API_KEY, FMP_API_KEY)
make docs SUBGRID=full                 # fetch reported financials -> docs/ (FMP, $0 model cost)
make outcomes SUBGRID=full             # compute Altman ground-truth labels
make all SUBGRID=full CONC=32          # capture both pairs in parallel + analyze
make tempsweep PAIR=openai_nano        # temperature robustness (repeat for gemini_flash)
make tempsweep PAIR=gemini_flash
make figures && make paper             # regenerate figures and fill the manuscript
```

`python3 status.py --subgrid full` shows live capture progress. Analysis (`make analyze render check`) is deterministic and free; only `make docs/outcomes/all/tempsweep` touch the network.

## Task is switchable

`config/task.yaml` selects the active task (`credit_health` by default; `earnings_surprise` and the original `directional` task are also defined). The flip / churn / agreement machinery is label-agnostic, so a new task is a config + prompt change.

## Citation

See `paper/paper_ieee_access.tex`. Data and code availability, pre-registration, and the amendments log are included in the manuscript.

## License

MIT (code) — see `LICENSE`.
