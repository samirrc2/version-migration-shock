# Model manifest

The two confirmatory migration pairs. Each pair is a vendor-declared "recommended
replacement": an incumbent version and the successor the vendor points deployments
to, with a published shutdown date for the incumbent (the forced-migration clock).
Prices are provider list prices ($/1M tokens) at data collection (July 2026);
knowledge cutoffs are as reported by the provider. Exact API strings are pinned and
are the object of record; `config/models.yaml` is the machine-readable source.

## Pair 1 — `openai_nano` (OpenAI)

| role | api string | price in/out | knowledge cutoff | incumbent shutdown |
|---|---|---|---|---|
| v_old | `gpt-5-nano-2025-08-07` | 0.05 / 0.40 | 2025-08-01 | 2026-12-11 |
| v_new | `gpt-5.4-nano` | 0.20 / 1.25 | 2025-08-31 | — |

## Pair 2 — `gemini_flash` (Google)

| role | api string | price in/out | knowledge cutoff | incumbent shutdown |
|---|---|---|---|---|
| v_old | `gemini-2.5-flash` | 0.30 / 2.50 | 2025-01-01 | 2026-10-16 |
| v_new | `gemini-3.5-flash` | 1.50 / 9.00 | 2025-05-01 | — |

## Notes

- Both successors are the same-family replacements named on the provider deprecation
  pages; `gemini_flash` has the tightest shutdown clock.
- A third pair (an xAI Grok migration) was scoped but awaits a publicly available
  vendor-declared successor; see the Threats to Validity section.
- OpenAI models are reasoning models: capture uses `max_tokens=2000`,
  `reasoning_effort=minimal`, and JSON-object response formatting (see
  `config/models.yaml` and `capture/agent.py`).
