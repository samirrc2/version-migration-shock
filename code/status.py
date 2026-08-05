"""Live capture progress. Reads the flushed CSV row counts (not stdout), so it shows
true percent completion even for a run whose logs are buffered.

  python3 status.py --subgrid full            # one snapshot
  python3 status.py --subgrid full --watch     # refresh every few seconds
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import loader as C
from _paths import repo_root

_RAW = repo_root() / "data" / "raw"


def rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as f:
        return max(0, sum(1 for _ in f) - 1)


def bar(frac: float, width: int = 28) -> str:
    n = int(frac * width)
    return "[" + "#" * n + "-" * (width - n) + "]"


def snapshot(subgrid: str) -> str:
    cfg = C.load_all()
    tickers, dates = C.subgrid(subgrid, cfg)
    n_rep = int(cfg["pairs"]["defaults"]["n_replicates"])
    total = len(tickers) * len(dates) * n_rep
    lines = [f"capture progress  (subgrid={subgrid}, {total} cells/version)"]
    grand_done = grand_tot = 0
    for pair in cfg["pairs"]["pairs"]:
        for v in ("v_old", "v_new"):
            done = rows(_RAW / f"runs_{pair['id']}_{v}.csv")
            frac = min(1.0, done / total) if total else 0.0
            grand_done += min(done, total); grand_tot += total
            lines.append(f"  {pair['id']:14s} {v:5s} {bar(frac)} {frac*100:5.1f}%  ({done}/{total})")
    gf = grand_done / grand_tot if grand_tot else 0.0
    lines.append(f"  {'TOTAL':14s} {'':5s} {bar(gf)} {gf*100:5.1f}%  ({grand_done}/{grand_tot})")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="full")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()
    if not args.watch:
        print(snapshot(args.subgrid)); return 0
    try:
        while True:
            print("\033[2J\033[H", end="")
            print(snapshot(args.subgrid), flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
