# Environment (Code Ocean–compatible)

`Dockerfile` pins the capsule environment that runs the **keys-free** reproduction
(Python 3.12 + `pyyaml`; `matplotlib` and the provider SDKs are only for the optional
figure rebuild and live re-collection).

## Capsule mounts

| Mount | Contents |
|-------|----------|
| `/code` | `analysis/`, `capture/`, `render/`, `config/`, `status.py`, `reproduce.sh`, `Makefile` |
| `/data` | `data/raw/` (frozen capture CSVs), `data/frozen/` (hash receipts), `data/outcomes/`, `docs/` (fundamentals) |
| `/results` | `claims_<pair>.json`, `results_<pair>.md` |

## Default Reproducible Run

```
bash reproduce.sh          # regenerate both migrations' results from frozen data (keys-free, $0)
bash reproduce.sh --verify # analyze each pair twice and hash-compare (determinism)
```

## Local development (no container)

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash reproduce.sh
```

Only the default keys-free path is needed to verify the article's numbers. Live
re-collection (`make all SUBGRID=full`) requires API keys at `../API Keys/keys.env.txt`
and incurs provider cost; it is not required for verification.
