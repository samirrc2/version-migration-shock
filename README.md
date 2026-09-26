# Version Migration as a Correlated Shock

Computational artifact for the IEEE Access article:

**Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems**

### Paper summary

Financial institutions deploying LLM agents inherit a risk absent from classical model governance: when the vendor updates the model, every deployment pinned to that version shifts behavior at once, involuntarily, and in a correlated direction. This article runs an identical, deterministic decision pipeline across **two real vendor migrations** on a credit-health classification task (SAFE / WATCH / DISTRESS, graded against Altman *Z''* bands) over **100 companies × 12 as-of dates × 3 replicates per version** (14,400 model calls), and measures the decision discontinuity induced purely by the update, net of within-version sampling noise.

**Main findings:**

- Both migrations produce a large, highly significant shock, but of **opposite character**. OpenAI (`gpt-5-nano-2025-08-07`→`gpt-5.4-nano`) flips **0.112** of assessments above the noise floor (95% CI [0.077, 0.149]) as genuine per-company reconsideration toward DISTRESS. Gemini (`gemini-2.5-flash`→`gemini-3.5-flash`) flips **0.381** (95% CI [0.302, 0.458]) as a wholesale distributional shift toward SAFE.
- The result survives the conservative max-of-both-versions noise floor (OpenAI 0.097 [0.06, 0.13]; Gemini 0.372 [0.30, 0.45]).
- Neither migration improves class-balanced accuracy; the Gemini shift **degrades** it toward chance (macro-F1 0.46→0.32). Both incumbents clear the 0.36 majority-class baseline (models are competent).
- The character of a migration shock does not generalize across vendors — an idiosyncratic, synchronized channel current model-risk guidance does not address (SR 26-2 places generative AI out of scope).

This repository is the frozen dataset and deterministic analysis pipeline that regenerates those numerical results, tables, and figures.

---

## 1. Artifact Identification

| Field | Value |
|-------|--------|
| **Article title** | Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent researchers |
| **Code repository** | https://github.com/samirrc2/version-migration-shock |
| **Persistent DOI** | https://doi.org/10.24433/CO.2874343.v1 (`10.24433/CO.2874343.v1`) |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: https://orcid.org/0009-0007-2779-3492; Robin Chawla: https://orcid.org/0009-0007-2807-3948 |

### Abstract and role of the artifact

This artifact accompanies a **pre-registered** study of vendor version-migration decision instability on a credit-health screening task. The confirmatory experiment comprises **14,400 independent model calls** (100 companies × 12 dates × 3 replicates × 2 versions × 2 migration pairs) using models from OpenAI and Google.

The artifact enables independent reproduction of the article's computational results. Specifically, it provides:

1. The frozen confirmatory dataset (`data/raw/runs_<pair>_v_{old,new}.csv`, each row carrying the model's raw response) with SHA-256 receipts (`data/frozen/`, aggregated in `DATA_MANIFEST.md`), the Altman ground-truth labels (`data/outcomes/ground_truth.json`), the reported-financials context (`docs/*.json`, optional for keys-free reproduce), and the study configuration (`code/config/`).
2. A deterministic analysis pipeline that regenerates the excess-flip-rate primary endpoint with cluster-bootstrap CIs, the prevalence/churn decomposition, three chance-corrected agreement statistics, class-balanced accuracy against the Altman ground truth, and the noise-floor and temperature sensitivities, into `results/claims_<pair>.json` and `results/results_<pair>.md`.
3. Pre-registration, its cryptographic freeze receipt, and the amendments log.
4. The capture and monitoring harness (the pre-migration parallel-run metric).

**Default workflow (this README):** regenerate all analysis outputs from the frozen dataset. This path requires **no API keys** and incurs **no inference cost**. Re-collecting the 14,400 API calls is optional, incurs cost, and is **not required** to verify the numerical claims in the article.

---

### Code Ocean capsule

A [Code Ocean](https://codeocean.com/) compute capsule for this artifact is available at
[https://doi.org/10.24433/CO.2874343.v1](https://doi.org/10.24433/CO.2874343.v1)
(DOI `10.24433/CO.2874343.v1`).

| Status | Detail |
|--------|--------|
| Capsule | Keys-free Reproducible Run via `/code/run` → `code/reproduce.sh` |
| Environment | `environment/Dockerfile` (Code Ocean `py-r` base + pinned pip; default path needs PyYAML) |
| Public link / DOI | https://doi.org/10.24433/CO.2874343.v1 |
| Local reproduce | `bash code/reproduce.sh` or `./code/run` |

The frozen dataset is committed to the repository, so the capsule reproduces every number with **no external download, no API keys, and no inference cost**.

---

## 2. Artifact Dependencies and Requirements

### Hardware

| Resource | Requirement |
|----------|-------------|
| CPU | Standard laptop or workstation (analysis is CPU-bound, single process) |
| RAM | ≥ 4 GB |
| Disk | ≥ 1 GB free (committed dataset ≈ 14 MB) |
| GPU | Not required |

### Operating system

- macOS, Linux, or Windows with WSL2
- `bash` required for `code/reproduce.sh` and `code/run`
- Containerized review environments (e.g., Code Ocean): Linux

### Software

| Component | Requirement |
|-----------|-------------|
| Python | ≥ 3.10 (3.10–3.13 accepted) |
| Shell | `bash` |
| Network | Not required for the default keys-free workflow |

### Software libraries

Dependencies are in `requirements.txt`. The **default reproduction path uses only PyYAML** — the analysis is otherwise pure Python standard library (verified in a clean PyYAML-only environment). The remaining packages are for optional figure rebuild and live re-collection:

- `pyyaml>=6.0` — configuration (required for reproduction)
- `matplotlib>=3.6` — optional, figure regeneration only
- `openai>=1.40`, `google-genai>=0.3` — optional, live re-collection only
- `requests` (via provider SDKs) — optional, live re-collection only

### Input data included with the artifact

| Path | Description | Approx. size |
|------|-------------|--------------|
| `data/raw/runs_<pair>_v_{old,new}.csv` | Frozen confirmatory call logs (incl. raw response) — 4 files | 8.7 MB |
| `data/raw/runs_<pair>_v_*_T{00,07,10}.csv` | Temperature-robustness subgrids — 12 files | included |
| `data/outcomes/ground_truth.json` | Altman *Z''* band labels the analysis grades against | < 1 MB |
| `docs/*.json` | Reported quarterly financials (no-lookahead context, 1,200 cells) | 4.7 MB |
| `data/frozen/*.freeze.json` | Per-capture SHA-256 receipts | < 1 MB |
| `code/config/` | Frozen task, model, pair, and grid configuration | < 1 MB |

**Integrity (frozen confirmatory captures):** SHA-256 of every CSV is recorded in `DATA_MANIFEST.md` and in the per-file receipts under `data/frozen/`. Example:

```
data/raw/runs_openai_nano_v_old.csv SHA-256 =
af1ace99c938a23ddba948d7df092763...   (full hash in DATA_MANIFEST.md)
```

### Optional dependencies (live re-collection only)

API credentials for OpenAI, Google Gemini, and Financial Modeling Prep are required **only** for live re-collection (`make -C code all SUBGRID=full`) and are read from `../API Keys/keys.env.txt`. They are **not** required for the default reproduction path, which runs entirely from the committed frozen dataset.

---

## 3. Installation and Deployment

### Time estimates

| Step | Typical duration |
|------|------------------|
| Create venv + install PyYAML (first time) | < 1 minute |
| Default reproduction (`bash code/reproduce.sh`, both pairs) | ~1 minute |
| Determinism check (`bash code/reproduce.sh --verify`) | ~2 minutes |
| Live re-collection of 14,400 calls (optional) | hours; provider-cost |

### Installation

```bash
git clone https://github.com/samirrc2/version-migration-shock.git
cd version-migration-shock
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
bash code/reproduce.sh
# or: ./code/run
```

No compilation step is required. On Code Ocean, packages come from `environment/Dockerfile` — no venv step. Capsule entry is `/code/run`.

### Deployment / execution

| Goal | Command |
|------|---------|
| Regenerate both migrations + gate-check (default) | `bash code/reproduce.sh` |
| Prove determinism (analyze twice, hash-compare) | `bash code/reproduce.sh --verify` |
| Analyze one pair | `python3 code/analysis/run.py --pair openai_nano` |
| Run the build gate only | `python3 code/render/check_claims.py` |
| Run unit tests | `python3 code/tests/test_metrics.py && python3 code/tests/test_stats.py` |
| Code Ocean entry point | `./code/run` (or thin `./run`; both → `code/reproduce.sh`) |
| Live re-collection (optional; **not** required to verify the paper) | `make -C code all SUBGRID=full` |

Outputs are written under `results/` as `claims_<pair>.json`, `results_<pair>.md`, and (when present) `tempsweep_<pair>.json` (the Code Ocean `/results` convention).

---

## 4. Reproducibility of Experiments

### Workflow

```text
data/raw/runs_<pair>_v_{old,new}.csv + data/outcomes/ground_truth.json + code/config/
        │
        ▼
  bash code/reproduce.sh
  (→ code/analysis/run.py per pair → code/render/report.py → code/render/check_claims.py)
        │
        ├── results/claims_<pair>.json     # every reported number, single source of truth
        ├── results/results_<pair>.md      # human-readable per-pair results report
        └── [check] OK                     # build gate: fails if any number ≠ frozen analysis
```

The primary endpoint is `excess_flip_rate = cross_version_flip_rate − within_version_flip_rate`, cluster-bootstrapped over tickers (2,000 draws, seed 42). `code/analysis/run.py` is a pure, seeded function of the frozen CSVs and configuration and produces byte-identical output on every re-run (`--verify` proves this).

### Expected results

After `bash code/reproduce.sh`, both pairs must pass the gate (`[check] OK — 64 required claims present`) and `results/claims_<pair>.json` must contain:

| Quantity | `openai_nano` | `gemini_flash` |
|----------|--------------:|---------------:|
| Matched cells | 3,490 | 3,600 |
| **Excess flip rate (primary)** | **0.1116** | **0.3806** |
| 95% CI (cluster bootstrap) | [0.0772, 0.1495] | [0.3025, 0.4583] |
| cross-version flip | 0.2166 | 0.3886 |
| within-version noise floor (pooled) | 0.1050 | 0.0081 |
| Excess vs conservative max floor | 0.0966 [0.060, 0.135] | 0.3725 [0.295, 0.451] |
| Marginal (rating-mix) shift | 0.0946 | 0.3186 |
| Churn (genuine) | 0.1221 | 0.0700 |
| Cohen κ / Scott π / Gwet AC1 | 0.60 / 0.60 / 0.70 | 0.33 / 0.27 / 0.47 |
| McNemar drift *p* | 5.67×10⁻¹⁸ | 1.39×10⁻⁵⁹ |
| Balanced accuracy old→new | 0.538→0.570 | 0.488→0.408 |
| Same-seed repeat-call floor (matched) | 0.0278 [0.0109, 0.0692] | 0.0139 [0.0038, 0.0492] |
| Excess vs matched floor (sensitivity) | 0.1888 | 0.3747 |
| Label-distribution distance (TVD) | 0.0946 [0.0597, 0.138] | 0.3186 [0.2411, 0.3944] |
| Excess on the 24 robustness cells | 0.1528 | 0.2222 |
| Restricted balanced acc. old→new | 0.5397→0.5383 | 0.4988→0.4052 |
| Restricted macro-F1 old→new | 0.5264→0.5319 | 0.4917→0.341 |
| Balanced-acc. Δ (95% CI) | 0.032 [-0.0046, 0.07] | -0.0801 [-0.1398, -0.0275] |
| Macro-F1 Δ (95% CI) | 0.0484 [0.0073, 0.0903] | -0.1383 [-0.2032, -0.0783] |
| Macro-F1 old→new (baseline 0.357) | 0.517→0.565 | 0.463→0.325 |

These are the same quantities reported in the article's Results section (Table 1). The determinism check must print `deterministic: byte-identical across re-runs`.

### Out of scope for the default workflow

- Re-issuing live model API calls (`make -C code all` / `code/capture/orchestrator.py`)
- Any inference or API spend
- Figure regeneration (requires matplotlib; not needed to verify the numbers)

---

## 5. Other Notes

- **Provider and regulatory provenance:** `docs/provenance/` holds the archived provider deprecation page behind Table 1 and the SR 26-2 guidance, each with a SHA-256 receipt.
- **Pre-registration and freeze records:** `PREREGISTRATION.md`, `PREREGISTRATION.freeze.txt`, `PREREGISTRATION_AMENDMENTS.md`
- **Model manifest and run playbook:** `docs/model_manifest.md`, `docs/STUDY_RUN.md`
- **Provenance:** every capture is SHA-256-stamped in `DATA_MANIFEST.md` and `data/frozen/*.freeze.json`; the frozen CSVs are the object of record and must not be regenerated (a correction requires a new versioned file plus a manifest changelog entry).
- **Anti-drift gate:** `code/render/check_claims.py` fails if any reported number disagrees with the frozen analysis, if a required claim (`code/config/slots.yaml`) is missing, or if any figure in `paper/main.tex` traces to no analysis output. External constants are allowlisted with a reason in `slots.yaml`.
- **Manuscript source:** official IEEE Access LaTeX under `paper/` (`paper/main.tex` is canonical; compiles to `paper/main.pdf`). Figures live only in `paper/figures/`.
- **Submission notes:** see `SUBMISSION_ARTIFACT.md` (GitHub + Code Ocean).
- **Issues and support:** GitHub Issues, or the author emails in Section 1.

### Repository structure

```text
version-migration-shock/
├── README.md                     LICENSE            requirements.txt
├── run                           # thin wrapper → code/run
├── DATA_MANIFEST.md              SUBMISSION_ARTIFACT.md   ARCHITECTURE.md
├── PREREGISTRATION.md  PREREGISTRATION.freeze.txt  PREREGISTRATION_AMENDMENTS.md
│
├── code/
│   ├── run                 # Code Ocean entry → reproduce.sh
│   ├── reproduce.sh        # keys-free analysis + gate
│   ├── analysis/           # metrics, stats, run.py, …
│   ├── capture/            # orchestrator, freeze, build_*
│   ├── render/             # report, check_claims, figures
│   ├── config/             # models, pairs, grid, slots, task
│   ├── tests/
│   ├── status.py  Makefile  run_all.sh  run_tempsweep.sh
│   ├── _paths.py           # repo_root() for data/docs/results
│   └── prompt_*.txt
├── environment/  Dockerfile + README  (Code Ocean capsule)
├── metadata/   metadata.yml
├── docs/       model_manifest.md, STUDY_RUN.md, and optional fundamentals JSON (live re-collection / label rebuild only; not needed for keys-free reproduce)
│
├── data/
│   ├── raw/       runs_<pair>_v_{old,new}.csv (+ temperature subgrids)  — frozen, committed
│   ├── frozen/    *.freeze.json  (SHA-256 receipts)
│   └── outcomes/  ground_truth.json  (Altman labels)
│
├── results/     claims_<pair>.json, results_<pair>.md, tempsweep_<pair>.json  (committed; Code Ocean /results)
├── paper/       IEEE Access manuscript (`main.tex` canonical) + figures/
└── submission/  upload set: main_manuscript.{pdf,docx}, highlighted_pdf.pdf,
                 IEEE-Access-Response-to-Reviewers.pdf  (bash submission/build_submission.sh)
```

`inputs/` (legacy price context for the inactive directional task) and generated artifacts (`logs/`, `.venv/`) are gitignored. Committed analysis outputs live under `results/`.

### Reproducing from a clean checkout

```bash
git clone https://github.com/samirrc2/version-migration-shock.git
cd version-migration-shock
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash code/reproduce.sh          # no API keys required
```

Both pairs should report `[check] OK`, and `results/claims_openai_nano.json` and `results/claims_gemini_flash.json` should match the Expected Results table in Section 4. `bash code/reproduce.sh --verify` repeats the analysis under three hash seeds and compares the output hashes.

## 6. License

MIT (code) — see `LICENSE`.
