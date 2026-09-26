# Catalogue of changes in this revision

`highlighted_pdf.pdf` highlights changed text inline, in yellow, and corresponds to
`submission/main_manuscript.pdf` page for page: both are 15 pages and all 15 start at the same point, so a
reader can hold them side by side. Highlighting is inline rather than block-level precisely so
that line and column breaking is untouched.

Changes inside tables and captions are not highlighted, because the markup cannot be applied
safely inside a tabular row. They are listed here instead, so that nothing in the revision is
unreported.

## 1. Changes inside floats, tables and captions

| Location | Change |
|---|---|
| Table 5 (governance mapping) | Rebuilt from three columns to five: a governance concept, then one column per framework, then how version migration breaks the concept and the proposed control. Both frameworks are given symmetrically — each cell carries the section number and the provision title as the guidance words it, rather than a bare section number. The five row concepts are vendor and third-party responsibility, ongoing monitoring, effective challenge and validation before use, model inventory and change control, and aggregate model risk. Provision titles are quoted from archived copies of both letters (`docs/provenance/SR1107.json`, `SR2602.json`), and `code/render/check_docs.py` fails if a printed name stops matching them, if the response letter's account of the table stops matching the table, or if either the letter or the caption misquotes or misnumbers the SR 26-2 footnote 3 scope carve-out. Caption rewritten to state that the SR 26-2 column gives the provisions that would otherwise apply. Set at `\small` like the paper's other tables, with ragged-right columns so the narrow text columns do not stretch. |
| Table 1 (migration pairs) | No content change. Surrounding prose now cites the archived provider capture. |
| Table 2 (main results) | Flip-conditional accuracy row corrected from `+0.124 / -0.179` to `+0.123 / -0.178`, a rounding correction. |
| Section III-C | No new displayed equation; the section reuses the existing `F_within`, `F_cross` and `F_excess` definitions. Its prose is highlighted. |
| Section III-D | One new displayed equation defining total variation distance. The equation itself is not highlighted; the prose around it is. |
| Bibliography | Reordered into first-citation order per the resubmission checklist; one entry removed (see item 3). |

## 2. Reference list reordering

The checklist asks that references be listed in order of citation. The bibliography was in
listing order, not citation order, with 33 of 35 positions differing. It is now in first-citation
order, which renumbers most citations in the text. Because this makes `latexdiff` interleave
markup across entry boundaries, the reference list is held constant across the diff used to build
the highlighted PDF; the highlighted PDF therefore shows the final, reordered list without
markup.

## 3. Deleted reference

Reviewer 1 noted that reference [24], J. Wei et al., "Emergent Abilities of Large Language
Models," does not support the sentence it was attached to. The citation and the bibliography entry
are both removed. No replacement was added.

## 4. Numbers corrected rather than added

Nine printed figures were rounded one place too far and are corrected. All nine come from a single
defect in `code/render/figures.py`, which rounded a value that had already been rounded to four
decimal places: 0.14948571 became 0.1495 and then 0.150, instead of 0.149. The underlying
analysis values never changed, and no finding, interval width or conclusion moves. The bug and
its fix were found by extending the build gate to `paper/main.tex`.

| Printed before | Printed now | Analysis value |
|---|---|---|
| `$[0.077,\,0.150]$` | `$[0.077,\,0.149]$` | 0.14948571 |
| `95\% CI: 7.7--15.0` | `95\% CI: 7.7--14.9` | the same bound as a percentage |
| `$[0.303,\,0.458]$` | `$[0.302,\,0.458]$` | 0.30245 |
| `95\% CI: 30.3--45.8` | `95\% CI: 30.2--45.8` | the same bound as a percentage |
| `$+0.124$` | `$+0.123$` | 0.12345679 |
| `[.077,.150]` (Table 2) | `[.077,.149]` | the same bounds as Section V-A |
| `[.303,.458]` (Table 2) | `[.302,.458]` | the same bounds as Section V-A |
| `.372\,[.30,.45]` (Table 2) | `.372\,[.29,.45]` | 0.2947 |
| `$-0.179$` | `$-0.178$` | -0.17849462 |

The first four are the excess-flip confidence bounds in Section V-A, printed there both as
proportions and as percentages. The next three are the corresponding cells in Table 2, which had
kept the superseded bounds after the prose was corrected. The remaining two are the
flip-conditional accuracy change, which appears both in Table 2 and in the Section V-E prose.

**These nine are deliberately not highlighted in the Highlighted PDF.** Each is the same quantity
at the same printed precision, so marking them would direct a reviewer to nine digit-level
corrections as though a result had moved. They are disclosed here instead, which is the same
treatment given to the reference list (reordered into citation order, also held constant across
the diff). `submission/build_highlighted.sh` holds both classes constant and fails if any of
them no longer appears in the previous version at the expected number of occurrences, so the table
above cannot go stale silently.

## 5. New gated claims

Twenty-five claim keys were added to `code/config/slots.yaml` and are emitted by the analysis
pipeline into `results/claims_<pair>.json`, so every new figure in the paper is checked against
the frozen analysis on each build. The required-claims count rises from 39 to 64.

The gate itself was extended: `code/render/check_claims.py` previously validated only the
generated report and did not read `paper/main.tex`. It now also fails if any figure in the
manuscript traces to no analysis output. External constants — the Altman thresholds, digits inside
model version strings, and the Code Ocean DOI — are allowlisted in `slots.yaml` with a reason.

## 6. Provenance added to the artifact

`docs/provenance/` is new and holds the two documentary sources the reviewers asked to have made
verifiable, each with a SHA-256 receipt and an extraction record:

- `google_deprecations_20260701.html` / `.json` — the archived provider deprecation page from
  1 July 2026, three days before the protocol-freeze date, recording `gemini-2.5-flash` with a
  shutdown date of 16 October 2026 and `gemini-3.5-flash` as the designated replacement.
- `SR2602.pdf` / `.json` — the SR 26-2 guidance, with the footnote 3 scope carve-out, the
  Section III aggregate-risk language and the Section VII vendor provisions quoted.
