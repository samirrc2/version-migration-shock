# Submission artifact (IEEE Access + Code Ocean)

Canonical manuscript: **`paper/main.tex`** (IEEE Access template). Submit from `main.tex`.
Analysis outputs live under **`results/`** (`claims_<pair>.json`, `results_<pair>.md`, `tempsweep_<pair>.json`).

## What reviewers / editors get

| Artifact | Location |
|----------|----------|
| Code + frozen data (14,400 calls) | https://github.com/samirrc2/version-migration-shock |
| SHA-256 of every CSV | `DATA_MANIFEST.md` + `data/frozen/*.freeze.json` |
| Keys-free reproduction | `./code/run` or `bash code/reproduce.sh` |
| Determinism check | `bash code/reproduce.sh --verify` |
| Code Ocean capsule | https://doi.org/10.24433/CO.2874343.v1 (`environment/Dockerfile`, `/code/run`) |

Raw CSVs are **committed** under `data/raw/`. Fundamentals under `docs/` are for
optional live re-collection / rebuilding labels; they are **not** required for
the default keys-free path (analysis uses `data/outcomes/ground_truth.json`).

## Paper wording

Data & Code Availability in `paper/main.tex` cites the GitHub URL and the Code
Ocean DOI `10.24433/CO.2874343.v1`
(\url{https://doi.org/10.24433/CO.2874343.v1}).

## Figures

Single source: **`paper/figures/`** (written by `python code/render/figures.py`).
Do not keep a duplicate root `figures/` tree.
