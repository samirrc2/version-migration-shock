# IEEE Access submission checklist — Paper 2

Audited `paper/main.tex` against the official IEEE Access template
(`ACCESS_latex_template_20260513`, the current 2026-05-13 version) and its embedded
author instructions. Status as of this audit.

| # | IEEE Access requirement | Status | Notes |
|---|---|---|---|
| 1 | Uses official `ieeeaccess.cls` | ✅ Done | Our `.cls` is **byte-identical** to the uploaded 2026-05-13 template |
| 2 | Title in title case (not ALL CAPS), no abbreviations | ✅ Done | "Version Migration as a Correlated Shock…" |
| 3 | Full author names, space between initials, `\authorrefmark` | ✅ Done | Samir Chincholikar, Robin Chawla |
| 4 | Affiliation `\address` with e-mail | ✅ Done | Independent Researcher + e-mails |
| 5 | Corresponding author (`\corresp`) | ✅ Done | Samir Chincholikar |
| 6 | `\PARstart` on first Introduction paragraph | ✅ Done | |
| 7 | Author biographies | ✅ Done | `IEEEbiographynophoto` for both (photos optional) |
| 8 | References in IEEE format, all attributed | ✅ Done | 34 refs, no author-less entries, no orphans |
| 9 | Figures/tables captioned and cross-referenced | ✅ Done | 3 figures, 5 tables, all `\ref`'d |
| 10 | `\EOD` before `\end{document}` | ✅ Done | |
| 11 | Abbreviations defined at first use | ✅ Done | LLM, GICS, JSON, API, SR 11-7/26-2 defined |
| 12 | `\history` / `\doi` placeholders present | ✅ Done | Filled by IEEE at publication |
| — | | | |
| 13 | **Abstract length 150–250 words** | ✅ Done | Trimmed 284 → **246 words**; all numbers preserved |
| 14 | **Keywords in alphabetical order** | ✅ Done | Reordered alphabetically |
| 15 | **Funding / support statement in `\tfootnote`** | ✅ Done | "…received no specific grant from any funding agency…" |
| 16 | **ORCID in author byline** | ✅ Done | Both ORCIDs added to the `\address` line |
| 17 | Abstract free of abbreviations | ◻ Minor | Uses "LLMs", "95% CI"; IEEE prefers none in abstract |
| 18 | Graphical abstract | ◻ Optional | Encouraged by IEEE Access, not required |
| 19 | `\IEEEmembership` tags | ◻ Optional | Only if authors are IEEE members |

## Status

Canonical submission file: **`paper/main.tex`**.

Data & Code Availability cites GitHub + Code Ocean DOI
`10.24433/CO.2874343.v1`. Author bios match the companion paper. Figures live
only under `paper/figures/`.

Optional (not required): graphical abstract, `\IEEEmembership` tags, and removing "LLMs"/"95\% CI"
from the abstract. The `\history`/`\doi` fields are IEEE-filled at publication.
