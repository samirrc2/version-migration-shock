# Environment (Code Ocean–compatible)

`Dockerfile` is the **Code Ocean** capsule environment (CO `py-r` base + pinned
pip packages). The **default keys-free** reproduction needs only `pyyaml`;
`matplotlib` and the provider SDKs are for optional figure rebuild / live
re-collection.

## Capsule mounts

| Mount | Contents |
|-------|----------|
| `/code` | Contents of repo `code/` (`run`, `reproduce.sh`, `analysis/`, `capture/`, `render/`, `config/`, …) |
| `/data` | Contents of repo `data/` (`raw/`, `frozen/`, `outcomes/`). Do **not** require `docs/` for the default keys-free run (fundamentals are only for optional live re-collection / rebuilding Altman labels). |
| `/results` | Written by `reproduce.sh`: `claims_<pair>.json`, `results_<pair>.md`, `tempsweep_<pair>.json`, plus `claims.json` and `PILOT_RESULTS.md` from the last pair analysed — eight files in all |

## What runs, and what a capsule cannot check

The capsule mounts `/code` and `/data` only, so the manuscript, README and reviewer response
are not present. The gates that read those files report that they are not checkable here and
are skipped; the analysis and the claims gate — the parts that actually regenerate and verify
the article's numbers — run in full. A capsule run therefore exits 0 on success.

The exit codes are a contract:

| Code | Meaning |
|------|---------|
| 0 | Every gate that applies to this copy passed |
| 1 | A gate failed: a reported number does not match the frozen analysis |
| 2 | The analysis reproduced, but a gate that *should* apply here could not run (a full checkout with the submission package not yet built). Never treat this as a pass. |

## Default Reproducible Run

Entry point: `/code/run` (cds to capsule root `/`, then `bash code/reproduce.sh`).

```
bash code/reproduce.sh          # regenerate both migrations' results from frozen data (keys-free, $0)
bash code/reproduce.sh --verify # analyze each pair twice and hash-compare (determinism)
./code/run                      # same as default path
```

## Local development (no container)

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash code/reproduce.sh
# or: ./code/run
```

Only the default keys-free path is needed to verify the article's numbers. Live
re-collection (`make -C code all SUBGRID=full`) requires API keys at
`../API Keys/keys.env.txt` and incurs provider cost; it is not required for verification.
