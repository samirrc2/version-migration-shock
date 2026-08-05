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
| `/results` | Written by `reproduce.sh` (`claims_*.json`, `results_*.md`) |

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
