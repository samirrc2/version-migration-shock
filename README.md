# Version Migration as a Correlated Shock

Computational artifact for the IEEE Access article:

**Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems**

### Paper summary

Financial institutions deploying LLM agents inherit a risk absent from classical model governance: when the vendor updates the model, every deployment pinned to that version shifts behavior at once, involuntarily, and in a correlated direction. This article runs an identical, deterministic decision pipeline across **two real vendor migrations** on a credit-health classification task (SAFE / WATCH / DISTRESS, graded against Altman *Z''* bands) over **100 companies × 12 as-of dates × 3 replicates per version** (14,400 model calls), and measures the decision discontinuity induced purely by the update, net of within-version sampling noise.

**Main findings:**

- Both migrations produce a large, highly significant shock, but of **opposite character**. OpenAI (`gpt-5-nano-2025-08-07`→`gpt-5.4-nano`) flips **0.112** of assessments above the noise floor (95% CI [0.077, 0.150]) as genuine per-company reconsideration toward DISTRESS. Gemini (`gemini-2.5-flash`→`gemini-3.5-flash`) flips **0.381** (95% CI [0.303, 0.458]) as a wholesale distributional shift toward SAFE.
- The result survives the conservative max-of-both-versions noise floor (OpenAI 0.097 [0.06, 0.13]; Gemini 0.372 [0.30, 0.45]).
- Neither migration improves class-balanced accuracy; the Gemini shift **degrades** it toward chance (macro-F1 0.46→0.32). Both incumbents clear the 0.36 majority-class baseline (models are competent).
- The character of a migration shock does not generalize across vendors — an idiosyncratic, synchronized channel current model-risk guidance does not address (SR 26-2 places generative AI out of scope).

This repository is the frozen dataset and deterministic analysis pipeline that regenerates those numbers, tables, and figures.

---

## 1. Artifact Identification

| Field | Value |
|-------|--------|
| **Article title** | Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent researchers |
| **Code repository** | https://github.com/samirrc2/version-migration-shock |
| **Persistent DOI** | Pending Zenodo / Code Ocean deposit (to be inserted when minted; anonymous review artifact per `SUBMISSION_ARTIFACT.md`) |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: https://orcid.org/0009-0007-2779-3492; Robin Chawla: https://orcid.org/0009-0007-2807-3948 |

### Role of the artifact

This artifact accompanies a **pre-registered** study of vendor version-migration decision instability. The confirmatory experiment comprises **14,400 independent model calls** (100 companies × 12 dates × 3 replicates × 2 versions × 2 migration pairs) using models from OpenAI and Google.

It enables independent reproduction of the article's computational results:

1. The frozen confirmatory dataset (`data/raw/runs_<pair>_v_{old,new}.csv`) with SHA-256 receipts (`data/frozen/`, aggregated in `DATA_MANIFEST.md`) and study configuration (`config/`).
2. A deterministic analysis pipeline that regenerates the excess-flip-rate endpoint with cluster-bootstrap CIs, the prevalence/churn decomposition, chance-corrected agreement statistics, class-balanced accuracy, and the noise-floor and temperature sensitivities under `claims_<pair>.json` / `results_<pair>.md`.
3. Pre-registration, its cryptographic freeze receipt, and the amendments log.
4. The capture and monitoring harness (the pre-migration parallel-run metric).

**Default workflow:** regenerate all analysis outputs from the frozen dataset. This path requires **no API keys** and incurs **no inference cost**. Re-collecting the 14,400 calls is optional, is costed, and is **not required** to verify the article's numerical claims.

---

## 2. Dependencies and Requirements

### Hardware

| Resource | Requirement |
|----------|-------------|
| CPU | Standard laptop/workstation (analysis is CPU-bound, single process) |
| RAM | ≥ 4 GB |
| Disk | ≥ 1 GB free (frozen CSVs are small; avoid ignored `logs/`) |
| GPU | Not required |

### Software

| Component | Requirement |
|-----------|-------------|
| Python | ≥ 3.10 |
| Shell | `bash` (for `reproduce.sh`) |
| Network | Not required for the default keys-free workflow |
| Libraries | `pyyaml` (analysis); `matplotlib` + `openai`, `google-genai`, `requests` only for optional figures / re-collection — see `code`-level `requirements.txt` and `environment/Dockerfile` |

---

## 3. Reproduce (keys-free, $0)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

bash reproduce.sh            # analyze both migrations from frozen data + gate-check
bash reproduce.sh --verify   # analyze each pair twice, hash-compare (determinism)
```

The build gate (`render/check_claims.py`) fails if any regenerated number disagrees with the frozen analysis. See `docs/STUDY_RUN.md` for the optional live-collection path.

---

## 4. Repository layout

```
config/     task.yaml, models.yaml, pairs.yaml, grid.yaml, loader.py, taskcfg.py, slots.yaml
capture/    orchestrator.py, agent.py, build_docs/inputs/outcomes.py, freeze.py, secrets.py
analysis/   metrics.py, stats.py, baseline.py, groundtruth.py, outcomes.py, tempsweep.py, run.py
render/     report.py (results report), check_claims.py (results gate)
data/frozen/            per-capture SHA-256 receipts
docs/       model_manifest.md, STUDY_RUN.md
environment/  Dockerfile + README (Code Ocean capsule)
metadata/   metadata.yml
PREREGISTRATION*.md   DATA_MANIFEST.md   reproduce.sh   Makefile
claims_<pair>.json, results_<pair>.md, tempsweep_<pair>.json   committed per-pair results
```

Raw model-capture CSVs (`data/raw/`) and fetched context (`inputs/`, `docs/*.json`) are released separately (large; hashes in `DATA_MANIFEST.md`) so a released dataset can be verified byte-for-byte. The manuscript (LaTeX + PDF) is maintained under `paper/` and is not part of this committed code artifact.

## 5. License

MIT (code) — see `LICENSE`.
