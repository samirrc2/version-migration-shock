# IEEE Access Submission Checklist — Audit (Paper 2)

Audited against the **official IEEE Access Submission Checklist** (18 items) and
the **official LaTeX template** `ACCESS_latex_template_20260513`. Manuscript
source: `paper/main.tex` → `paper/main.pdf` (15 pp.) + `paper/main.docx`.

Legend: ✅ Done (verified in folder) · 👤 Author action (submission portal / attestation, not a file) · ➖ N/A

## Official 18-point checklist

| # | Requirement | Status | Evidence / notes |
|---|-------------|--------|------------------|
| 1 | Double-column, single-spaced, **required IEEE Access template**; Word **and** PDF, content matching, < 40 MB | ✅ Done | `ieeeaccess.cls` is **byte-identical** to the official template (md5 `6e473d2a…`). PDF 15 pp, double-column. `main.docx` regenerated to match the PDF. Sizes: PDF 530 KB, DOCX 149 KB. |
| 2 | (Duplicate of 1 — template + matching source/PDF) | ✅ Done | Same as #1. DOCX now contains every section incl. funding note, Index Terms, both bios, all numbers, 3 figures, 5 tables. |
| 3 | Author list finalized; non-authors → Acknowledgment | ✅ Done | Two authors (Chincholikar, Chawla). Acknowledgment section present. 👤 Confirm the list is final before submission — post-submission changes need editor approval. |
| 4 | Submitting author has **public, populated ORCID** | ✅ / 👤 | ORCID `0009-0007-2779-3492` in byline. 👤 Verify it is public + populated in your ORCID profile and linked in the submission account. |
| 5 | All authors on **both** source file and PDF; system extracts full list | ✅ Done | Both authors in `\author{}` (source) and in the PDF/DOCX. 👤 Confirm ScholarOne extracts both at upload. |
| 6 | Short biographies for **all** authors, below references | ✅ Done | Two `\IEEEbiography` blocks after the bibliography, each with a black-and-white author photograph cropped to the template's 1.0 in × 1.25 in area; present in the DOCX too (`check_docs.py` fails if the two formats stop carrying the same images). |
| 7 | Grammar reviewed (Paperpal Preflight offered) | ✅ / 👤 | Prose is clean and consistent. 👤 Optional: run Paperpal Preflight for a final pass. |
| 8 | References accurate, relevant, none retracted | ✅ Done | 34 references, **all cited**, no orphans, no broken keys. Author-less entries previously fixed. 👤 Final retraction spot-check recommended. |
| 9 | Not under submission elsewhere | 👤 | Author attestation — not verifiable from files. |
| 10 | Supplementary material ready | ✅ Done | Code + frozen data on GitHub and a Code Ocean capsule (DOI `10.24433/CO.2874343.v2`), cited in Data & Code Availability. |
| 11 | Abbreviations defined at first use (even if in abstract) | ✅ Done (1 minor) | LLM defined in abstract + body; API, GICS spelled out; SR 11-7/26-2 contextual. **Minor:** "JSON" is not expanded at first use — optional to spell out once. |
| 12 | 3–10 keywords | ✅ Done | **9 keywords**, alphabetical. |
| 13 | Select a manuscript type | 👤 | Select **"Research Article"** at submission (hypothesis + experiment + result). |
| 14 | Opposed reviewers list (if any) | ➖ | Optional; none required. |
| 15 | Video (≤ 100 MB) ready if applicable | ➖ | No video. |
| 16 | "List of updates" if resubmitting after reject | ➖ | Fresh submission — not applicable. |
| 17 | Keep under ~20 pages | ✅ Done | **14 pages.** |
| 18 | No "Lena image" | ✅ Done | Not used. |

## LaTeX format audit (against `ACCESS_latex_template_20260513`)

| Element | Status | Notes |
|---------|--------|-------|
| `\documentclass{ieeeaccess}` + official `.cls` | ✅ | Byte-identical cls (md5 `6e473d2a…`). |
| `\history{}` / `\doi{}` placeholders | ✅ | Present; IEEE fills these at publication. |
| Title (title case, no abbreviations except LLM) | ✅ | Contains "LLM"; defined in abstract. |
| `\author` + `\uppercase` + `\authorrefmark` | ✅ | Both authors, correct markup. |
| `\address[1]` with e-mail **and ORCID** | ✅ | Both e-mails + both ORCIDs. |
| `\tfootnote` funding/no-grant statement | ✅ | "…received no specific grant…" + submission date. |
| `\markboth` running heads | ✅ | Short-title running head. |
| `\corresp` corresponding author | ✅ | Robin Chawla (e-mail + ORCID `0009-0007-2807-3948`). |
| `\begin{abstract}` length 150–250 words | ✅ | **243 words.** |
| `\begin{keywords}` (Index Terms) | ✅ | 9, alphabetical. |
| `\PARstart` on first Introduction paragraph | ✅ | Present. |
| Figures captioned + `\ref`'d | ✅ | 3 figures (fig1–3), all referenced. |
| Tables captioned + `\ref`'d | ✅ | 5 tables (models, main, mix, gov, temp), all referenced. |
| `\begin{thebibliography}` IEEE style | ✅ | 34 `\bibitem`, numeric, no orphans. |
| `\IEEEbiography` × 2, after refs | ✅ | **Required** by the IEEE Access resubmission checklist ("the revised manuscript … with all author biographies and photos included"); both supplied, grayscale, 1.0 × 1.25 in. |
| `\EOD` before `\end{document}` | ✅ | Present. |
| Compiles cleanly | ✅ | 15-page PDF, double-column US-letter. |

## Pending / open items

**In the folder:** nothing pending. The only stale artifact — `main.docx` (predated the
funding note + Use-of-Generative-AI section) — has been **regenerated** and now matches
the PDF. PDF and DOCX are in sync.

**Requires you at the submission portal (cannot be done from files):**

1. Manuscript type → **Research Article** (item 13).
2. Confirm ORCID is **public + populated** and linked to the submitting account (item 4).
3. Attest the paper is **not under review elsewhere** (item 9).
4. Optional: run **Paperpal Preflight** grammar check (item 7).

**Optional polish (not blockers):** spell out "JSON" once (item 11); consider a graphical
abstract and `\IEEEmembership` tags (both optional); remove "LLMs"/"95% CI" from the
abstract if you want zero abbreviations there.

**Housekeeping:** `paper/figures/fig4_sector.png` exists but is **not referenced** in
`main.tex` (leftover from a removed figure) — safe to delete for a cleaner repo.

---

# Resubmission audit (against the official Resubmission Checklist, 6.26.23)

This revision responds to two reviewers. Audited against the official resubmission checklist,
not the first-submission checklist above.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | All Editor and reviewer comments addressed | Done | 12 concerns (Reviewer 1: 3, Reviewer 2: 9). Each has a concern / response / action entry in `submission/response_to_reviewers.txt`. Two led to new analysis, three to weakened claims, one to a deleted reference. |
| 2 | Grammar reviewed | Done / author action | Prose reviewed on every changed passage. Optional: run Paperpal Preflight for a final pass. |
| 3 | Math formatted per IEEE guidelines | Done | Audited: no multi-letter variable set in italic (all use `\mathrm`), no asterisk as a multiplication sign, no unit adjacent to a number without a space, no vectors requiring bold. The `y^{*}` superscripts are reference-label markers, not multiplication. |
| 4 | References accurate and in citation order | Done | Reordered into first-citation order; 33 of 35 positions previously differed. One orphaned entry removed (Reviewer 1, Concern 3). 34 bibitems, 34 cited, no orphans. |
| 5 | Video included in peer review | N/A | No video. |
| 6 | Response to Reviewers document | Done | `submission/IEEE-Access-Response-to-Reviewers.docx` for upload under "Author's Response Files", with PDF and plain-text copies. Follows the official template structure: reviewer concern, author response, author action. |
| 7 | Manuscript with all individual changes highlighted | Done | `submission/highlighted_pdf.pdf`, 15 pp — the same length as `paper/main.pdf`, and carrying exactly the same text (verified: both extract to 65,942 alphanumeric characters, and the revision rebuilds from the diff markup at similarity 1.000000). Changed text is highlighted inline in yellow. Inline highlighting keeps the layout close but not identical: `soul`'s `\texthl` alters a few line breaks, so nine of the fifteen pages begin at the same point as the clean PDF and six do not. Nothing is added or lost. Built by `submission/build_highlighted.sh`. Changes inside tables and captions cannot be highlighted safely and are catalogued in `submission/CHANGES.md`. |
| 8 | Supplementary materials | N/A as a separate upload | Code and frozen data are on GitHub and in the Code Ocean capsule, cited in Data and Code Availability. Nothing additional is needed as a `.zip`. |
| 9 | Main Manuscript (Word or LaTeX) with biographies | Done | `paper/main.tex` and `paper/main.docx`, regenerated so the two match. Both biographies present. |
| 10 | Main Manuscript PDF, double column, single spaced | Done | `submission/main_manuscript.pdf`, 15 pp, double column. |
| 11 | Byline change request | Not required | Author list unchanged (Chincholikar, Chawla). The byline-change form is to be disregarded when authorship has not changed. |

## Manuscript ID

`submission/response_to_reviewers.txt` carries a placeholder on its first line:
`Access-2026-XXXXX`. Fill this in from the decision letter before uploading.

## Resubmission route

The checklist states that a resubmission goes through the IEEE Author Portal **as a new
manuscript**, and that the original reviewers may not be available. The response document is
therefore written so that it is intelligible to a reviewer who never saw the first version: each
entry restates the concern before answering it.

## What changed in the artifact

- `code/analysis/` gained the matched repeat-call baseline, the total variation distance, the
  subgrid reconciliation and the restricted class-balanced metrics with bootstrap intervals.
- `code/config/slots.yaml` required-claims rises from 39 to 64, so every new figure is gated.
- `code/render/check_claims.py` now also gates `paper/main.tex`. It previously validated only
  the generated report, which is how two rounding errors survived to submission.
- `docs/provenance/` is new: the archived provider deprecation page and the SR 26-2 guidance,
  each with a SHA-256 receipt.
- The pipeline still reproduces byte-identically (`bash code/reproduce.sh --verify`).
