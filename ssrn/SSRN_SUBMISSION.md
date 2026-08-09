# SSRN preprint submission — metadata sheet

Everything below is ready to paste into the SSRN "Submit a Paper" form.
The uploaded PDF is `Version-Migration-Correlated-Shock_SSRN.pdf` — a **neutral
single-column preprint** (23 pages) with **no IEEE Access template, header, DOI,
or branding**. It has the same text, numbers, equations, tables, figures, and
references as the journal version, rendered in a plain `article` layout suitable
for a preprint. (Built by `build_preprint.py` from `../paper/main.tex`; source is
`preprint.tex`.) Nothing in the repo, data, results, or Code Ocean capsule is
affected by this folder — it is a self-contained submission package.

---

## Title
Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems

## Authors (byline order)
1. Samir Chincholikar — Independent Researcher — samir.chincholikar@gmail.com — ORCID 0009-0007-2779-3492
2. Robin Chawla — Independent Researcher — robin.chawla.cse14@iitbhu.ac.in — ORCID 0009-0007-2807-3948 — **Corresponding author / submitting author**

> SSRN note: the account that submits should be Robin's (corresponding author),
> and each co-author should be added with their email so SSRN links the paper to
> both author profiles. First-author order (Samir first) is preserved.

## Abstract (plain text — paste into the Abstract field)
See `abstract.txt` (single paragraph, 243 words, no math markup). SSRN's abstract
field accepts plain text only, so the copy in `abstract.txt` already has the LaTeX
symbols removed and en-dashes converted.

## Keywords (paste into Keywords field, comma-separated)
Algorithmic monoculture, credit risk, financial artificial intelligence, large language models, model drift, model risk management, model version migration, reproducible evaluation, third-party model risk

## JEL Classification Codes (Finance / Economics — SSRN requests these)
- G17 — Financial Forecasting and Simulation
- G21 — Banks; Depository Institutions; Credit
- G28 — Financial Institutions: Government Policy and Regulation
- G32 — Financing Policy; Financial Risk and Risk Management
- C52 — Model Evaluation, Validation, and Selection
- O33 — Technological Change: Choices and Consequences; Diffusion Processes

## Manuscript / paper type
Working Paper (preprint). Not yet published; concurrently submitted to IEEE Access.

## Suggested SSRN networks / eJournals to classify under
- Risk Management & Analysis in Financial Institutions (Banking & Insurance)
- Financial Engineering
- Machine Learning eJournal / Artificial Intelligence
- Econometrics: Applied Econometrics & Modeling (for the evaluation methodology)

## Data & code availability (for the "Additional Information" / cover note)
Code and frozen data: https://github.com/samirrc2/version-migration-shock
Reproducible capsule (Code Ocean, keys-free): https://doi.org/10.24433/CO.2874343.v1

## Suggested citation (until an SSRN ID is assigned)
Chincholikar, S., & Chawla, R. (2026). Version Migration as a Correlated Shock:
Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems.
Working paper. Available at SSRN.

---

## Pre-submission checklist
- [ ] PDF uploaded: `Version-Migration-Correlated-Shock_SSRN.pdf`
- [ ] Title entered exactly as above (title case)
- [ ] Both authors added with emails + ORCIDs; Robin set as submitting/corresponding
- [ ] Abstract pasted from `abstract.txt`
- [ ] Keywords pasted
- [ ] JEL codes entered
- [ ] Paper type = Working Paper
- [ ] Data/code links added to the cover note
- [ ] Confirm concurrent-submission policy is acceptable to IEEE Access (preprints
      are generally permitted; verify in the IEEE Access author terms before posting)

## Notes
- The submission PDF is the **neutral preprint** (no IEEE branding), as required
  for a preprint. The IEEE Access-formatted `paper/main.pdf` is NOT used here.
- The only occurrence of "IEEE" in the preprint is inside a reference citation
  ("Proc. IEEE/CVF Conf. ...") — a legitimate venue name, not journal branding.
- The abstract is 243 words, within SSRN's field limits.
- To regenerate the preprint after any edit to `paper/main.tex`:
  `python3 ssrn/build_preprint.py && (cd ssrn && pdflatex preprint.tex)`.
