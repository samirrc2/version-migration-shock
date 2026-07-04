# Pre-registration Amendments Log

The frozen PREREGISTRATION.md (credit-health task; SHA-256 in
PREREGISTRATION.freeze.txt) is never edited. Post-freeze changes are logged here.

## Study revamp (2026-07-04)

The study was moved from a directional buy/hold/sell price task to a credit-health
classification task (SAFE/WATCH/DISTRESS from reported quarterly financials, graded
against Altman Z'' bands). Rationale: the directional task is a domain where no model
has skill (accuracy is near chance), which invites a "toy task / ecological validity"
critique; credit-risk screening from financial statements is a genuine, widely
deployed LLM use case with an objective, reproducible ground truth. The directional
pre-registration is withdrawn (retained in version history).

Because the new pre-registration is frozen BEFORE any credit-task model call, the
credit study carries no amendments: the primary endpoint, all secondaries (including
the instability dose-response and the Altman-band accuracy analysis), the decision
rule, and the ground truth are all pre-specified and confirmatory for both pairs.

(Future post-freeze additions, if any, will be logged below, dated, and labeled
exploratory/non-gating.)
