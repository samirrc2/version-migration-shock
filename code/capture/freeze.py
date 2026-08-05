"""Freeze-on-landing: hash and lock one capture the moment it completes. Writes
data/frozen/<pair>_<version>.freeze.json with the SHA-256 of the raw CSV and makes
the CSV read-only."""
from __future__ import annotations
import argparse, hashlib, json, os, stat, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import repo_root

_ROOT = repo_root()
_RAW = _ROOT / "data" / "raw"
_FROZEN = _ROOT / "data" / "frozen"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--version", required=True, choices=["v_old", "v_new"])
    ap.add_argument("--tag", default="", help="suffix, e.g. _T07, to freeze a sweep CSV")
    args = ap.parse_args()

    csv_path = _RAW / f"runs_{args.pair}_{args.version}{args.tag}.csv"
    if not csv_path.exists():
        print(f"[freeze] ERROR: {csv_path} not found — capture first.")
        return 2
    _FROZEN.mkdir(parents=True, exist_ok=True)
    digest = sha256(csv_path)
    n_rows = sum(1 for _ in csv_path.open()) - 1
    receipt = {
        "pair": args.pair, "version": args.version, "tag": args.tag,
        "csv": csv_path.name, "sha256": digest, "n_rows": n_rows,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
    }
    (_FROZEN / f"{args.pair}_{args.version}{args.tag}.freeze.json").write_text(json.dumps(receipt, indent=2))
    try:
        os.chmod(csv_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass
    print(f"[freeze] {csv_path.name}  sha256={digest[:16]}...  rows={n_rows}  -> receipt written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
