"""Build the objective ground-truth file data/outcomes/ground_truth.json, keyed
"TICKER|DATE" -> label/sign, for the ACTIVE task:

  altman_z        : credit-health band (SAFE/WATCH/DISTRESS) from the frozen docs/
                    (reproducible, no network).
  forward_return  : sign of the realized 20-trading-day forward return (needs FMP prices).
  earnings_surprise: BEAT/MEET/MISS from actual vs estimated EPS (needs FMP calendar).

  python capture/build_outcomes.py --subgrid full
"""
from __future__ import annotations
import argparse, json, sys, time, threading
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
import secrets as secretstore
import loader as C
import taskcfg
import groundtruth as GT

_ROOT = Path(__file__).resolve().parent.parent
_OUT = _ROOT / "data" / "outcomes"
_DOCS = _ROOT / "docs"


def _altman(tickers, dates) -> dict:
    out = {}
    n_ok = 0
    for t in tickers:
        for d in dates:
            f = _DOCS / f"{t}_{d}.json"
            label = None
            if f.exists():
                fin = json.loads(f.read_text()).get("fin", {})
                label = GT.band_from_fin(fin)
            out[f"{t}|{d}"] = label
            n_ok += label is not None
    print(f"[outcomes] altman_z: {n_ok}/{len(out)} labeled from docs/")
    return out


def _forward_return(tickers, dates, key) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    from build_inputs import fetch_history
    fwd = int(C.load_all()["grid"]["forward_return_days"])
    lo = (date.fromisoformat(min(dates)) - timedelta(days=10)).isoformat()
    hi = (date.fromisoformat(max(dates)) + timedelta(days=int(fwd * 1.6) + 15)).isoformat()
    out, lock = {}, threading.Lock()

    def sign(series, d):
        idx = [i for i, r in enumerate(series) if r["date"] >= d]
        if not idx or idx[0] + fwd >= len(series):
            return None
        p0, p1 = series[idx[0]]["close"], series[idx[0] + fwd]["close"]
        if p0 <= 0:
            return None
        r = p1 / p0 - 1
        return 1 if r > 0 else (-1 if r < 0 else 0)

    def work(t):
        try:
            s = fetch_history(t, lo, hi, key)
        except Exception as e:
            print(f"  ! {t}: {type(e).__name__}: {str(e)[:70]}"); s = []
        loc = {f"{t}|{d}": (sign(s, d) if s else None) for d in dates}
        with lock:
            out.update(loc)
        time.sleep(0.2)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(work, tickers))
    print(f"[outcomes] forward_return: {sum(1 for v in out.values() if v is not None)}/{len(out)} realized")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="full")
    args = ap.parse_args()
    tickers, dates = C.subgrid(args.subgrid)
    _OUT.mkdir(parents=True, exist_ok=True)
    gt = taskcfg.GROUND_TRUTH
    print(f"[outcomes] task={taskcfg.NAME} ground_truth={gt}")
    if gt == "altman_z":
        data = _altman(tickers, dates)
    elif gt == "forward_return":
        key = secretstore.get_raw("FMP_API_KEY")
        if not key:
            print("[outcomes] ERROR: FMP_API_KEY not found"); return 2
        data = _forward_return(tickers, dates, key)
    else:
        print(f"[outcomes] ERROR: ground_truth '{gt}' not implemented yet."); return 2
    (_OUT / "ground_truth.json").write_text(json.dumps(data, indent=2))
    realized = sum(1 for v in data.values() if v is not None)
    print(f"[outcomes] wrote {realized}/{len(data)} -> {_OUT/'ground_truth.json'}")
    return 0 if realized else 2


if __name__ == "__main__":
    sys.exit(main())
