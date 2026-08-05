"""Config loader. A condition = one deterministic decision-generator (resolved
model entry + temperature + seed_policy + n_replicates). A migration pair is two
conditions differing only in model."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

_HERE = Path(__file__).resolve().parent


def _load(name: str) -> dict:
    return yaml.safe_load((_HERE / name).read_text())


@dataclass(frozen=True)
class Condition:
    pair_id: str
    version: str
    model_key: str
    model_cfg: dict
    temperature: float
    seed_policy: str
    n_replicates: int
    unit: str


def load_all() -> dict:
    return {"models": _load("models.yaml")["models"],
            "pairs": _load("pairs.yaml"),
            "grid": _load("grid.yaml")}


def conditions_for_pair(pair_id: str, cfg: dict | None = None) -> list[Condition]:
    cfg = cfg or load_all()
    models = cfg["models"]
    pairs = cfg["pairs"]
    d = pairs["defaults"]
    pair = next((p for p in pairs["pairs"] if p["id"] == pair_id), None)
    if pair is None:
        raise KeyError(f"unknown pair {pair_id!r}; have {[p['id'] for p in pairs['pairs']]}")
    out = []
    for version in ("v_old", "v_new"):
        mkey = pair[version]
        if mkey not in models:
            raise KeyError(f"pair {pair_id} {version} references unknown model {mkey!r}")
        out.append(Condition(
            pair_id=pair_id, version=version, model_key=mkey,
            model_cfg=dict(models[mkey]),
            temperature=float(d["temperature"]),
            seed_policy=str(d["seed_policy"]),
            n_replicates=int(d["n_replicates"]),
            unit=str(d["unit"]),
        ))
    return out


def subgrid(name: str, cfg: dict | None = None) -> tuple[list[str], list[str]]:
    cfg = cfg or load_all()
    sg = cfg["grid"]["subgrids"][name]
    return list(sg["tickers"]), list(sg["dates"])


if __name__ == "__main__":
    c = load_all()
    print("models:", list(c["models"]))
    print("pairs :", [p["id"] for p in c["pairs"]["pairs"]])
    for cond in conditions_for_pair(c["pairs"]["pilot"]["pair"], c):
        print(f"  {cond.pair_id} {cond.version} -> {cond.model_key} "
              f"(T={cond.temperature}, reps={cond.n_replicates}, unit={cond.unit})")
