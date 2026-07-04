# Preparing the anonymous review artifact (issue #4)

The paper's Data & Code Availability section promises an anonymous artifact **during
review** plus an embargoed raw-data deposit. Two short steps produce both; do them
before submitting and paste the resulting URLs into the paper where it currently reads
`[anonymized repository URL]`.

## 1. Anonymous code repository (this repo, scrubbed)

Anonymize a snapshot of this repository (code + results + manifests; the raw `data/raw/`
CSVs go to Zenodo in step 2, not here).

1. Scrub identity from the working tree:
   - `LICENSE` — replace `Copyright (c) 2026 The Authors` (already generic; confirm no name).
   - `README.md`, `DATA_MANIFEST.md` — no author names (confirm).
   - Remove git history that carries your name/email: publish from a fresh history, not your
     personal commits (see the squash command below).
2. Publish anonymously. Two common routes:
   - **anonymous.4open.science** — paste your GitHub repo URL; it serves a read-only,
     name-stripped mirror with a citable anonymous link. Easiest for double-blind.
   - **A scrubbed GitHub repo** under a throwaway handle, with a squashed single commit:
     ```
     git checkout --orphan review
     git add -A
     git commit -m "Anonymous review artifact"
     git push throwaway review:main
     ```
3. Put the anonymous URL in the paper (`paper_ieee_access.tex` and `manuscript.md`,
   the `[anonymized repository URL]` placeholder).

## 2. Embargoed raw-data deposit (Zenodo)

The raw per-call model responses (`data/raw/*.csv`, ~14,400 rows across both pairs) are the
object of record and are too large / not committed to git. Deposit them under embargo:

1. zenodo.org → New upload → add `data/raw/*.csv` plus a copy of `DATA_MANIFEST.md`.
2. Access = **Restricted / Embargoed**; enable a **reviewer / shared access link** (a token URL).
3. Reserve the DOI now (Zenodo lets you reserve before publishing) so it can be cited; keep the
   record embargoed until acceptance.
4. Put the **reviewer access token URL** in the submission system's confidential-to-editors field,
   and reference "embargoed Zenodo record, token in submission system" in the paper (already worded
   that way).

## 3. Verifiability check the reviewer can run

The point of the manifest is that a reviewer with the token can prove the released data produced the
reported numbers:
```
shasum -a 256 data/raw/runs_openai_nano_v_old.csv     # matches DATA_MANIFEST.md
make analyze PAIR=openai_nano && make render && make check   # regenerates + gate-checks every claim
```

## On acceptance

De-anonymize the repo (restore author identity, real remote), lift the Zenodo embargo, and replace
the anonymous URL + "to be released on acceptance" wording with the public DOI.
