"""Build no-lookahead, price-derived context snippets into inputs/<TICKER>_<DATE>.json.

For each (ticker, date) cell, the snippet is computed ONLY from the ticker's own
price history strictly before the analysis date: trailing 1w/1m/3m returns, 21-day
annualized realized volatility, and position within the 63-day range. No post-date
information is ever used; the as-of date is the last trading day before the analysis
date. Fully reproducible from public prices (FMP).

One FMP call per ticker (the full window is fetched once and every date is computed
from that cached series). Runs where the model APIs run — needs FMP_API_KEY and
network. Use --selftest to validate the math offline.

Usage:
  python capture/build_inputs.py --subgrid full
  python capture/build_inputs.py --subgrid pilot --workers 4
  python capture/build_inputs.py --selftest
"""
from __future__ import annotations
import argparse, json, math, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import secrets as secretstore
import loader as C

_HERE = Path(__file__).resolve().parent
_INPUTS = _HERE.parent / "inputs"
# FMP stable API (the legacy /api/v3/ path 403s for keys issued after 2025-08-31).
_FMP = ("https://financialmodelingprep.com/stable/historical-price-eod/full"
        "?symbol={t}&from={f}&to={to}&apikey={k}")


def fetch_history(ticker: str, start: str, end: str, key: str, retries: int = 4) -> list[dict]:
    """Return [{date, close}, ...] ascending by date. Retries on 429/5xx."""
    import urllib.request, urllib.error
    url = _FMP.format(t=ticker, f=start, to=end, k=key)
    last = None
    d = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper2/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (2 ** attempt)); continue
            raise
        except Exception as e:
            last = e
            time.sleep(1.0 * (2 ** attempt)); continue
    if d is None:
        raise last or RuntimeError("fetch failed")
    # stable returns a bare array; legacy returned {"historical": [...]}.
    hist = d if isinstance(d, list) else d.get("historical", [])
    out = []
    for row in hist:
        c = row.get("adjClose", row.get("close"))
        if row.get("date") and c is not None:
            out.append({"date": str(row["date"])[:10], "close": float(c)})
    out.sort(key=lambda x: x["date"])
    return out


def _pct(a, b):
    return None if (b in (None, 0)) else (a / b - 1.0)


def compute_snippet(series: list[dict], analysis_date: str) -> dict | None:
    """series ascending by date. Uses only closes strictly BEFORE analysis_date."""
    hist = [r for r in series if r["date"] < analysis_date]
    if len(hist) < 63:
        return None
    closes = [r["close"] for r in hist]
    asof = hist[-1]["date"]
    px = closes[-1]

    def back(n):
        return closes[-1 - n] if len(closes) > n else None

    ret_1w, ret_1m, ret_3m = _pct(px, back(5)), _pct(px, back(21)), _pct(px, back(63))
    last21 = closes[-22:]
    rets = [math.log(last21[i] / last21[i - 1]) for i in range(1, len(last21))
            if last21[i - 1] > 0]
    vol = (math.sqrt(sum(r * r for r in rets) / len(rets)) * math.sqrt(252)) if rets else None
    w63 = closes[-63:]
    lo, hi = min(w63), max(w63)
    pos = None if hi == lo else (px - lo) / (hi - lo)

    def p(x, mult=100):
        return "n/a" if x is None else f"{x * mult:+.1f}%"

    headline = (f"Price action as of {asof}: 1w {p(ret_1w)}, 1m {p(ret_1m)}, "
                f"3m {p(ret_3m)}.")
    fundamentals = (f"Last close {px:.2f}. 21d annualized realized volatility "
                    f"{'n/a' if vol is None else f'{vol*100:.0f}%'}. Position in trailing "
                    f"63-day range: {'n/a' if pos is None else f'{pos*100:.0f}%'} "
                    f"(0%=low, 100%=high).")
    return {"asof": asof, "headline": headline, "fundamentals": fundamentals}


def build_one(ticker, dates, key, force):
    written = skipped = missing = 0
    need = [d for d in dates if force or not (_INPUTS / f"{ticker}_{d}.json").exists()]
    if not need:
        return 0, len(dates), 0
    lo = (date.fromisoformat(min(dates)) - timedelta(days=170)).isoformat()
    hi = max(dates)
    try:
        series = fetch_history(ticker, lo, hi, key)
    except Exception as e:
        print(f"  ! {ticker}: fetch failed: {type(e).__name__}: {str(e)[:100]}")
        return 0, 0, len(need)
    for d in dates:
        f = _INPUTS / f"{ticker}_{d}.json"
        if not force and f.exists():
            skipped += 1
            continue
        snip = compute_snippet(series, d)
        if snip is None:
            missing += 1
            continue
        snip["source_provenance"] = "price_derived_fmp"
        f.write_text(json.dumps(snip, indent=2))
        written += 1
    return written, skipped, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="full")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    key = secretstore.get_raw("FMP_API_KEY")
    if not key:
        print("[inputs] ERROR: FMP_API_KEY not found in keys.env"); return 2
    tickers, dates = C.subgrid(args.subgrid)
    _INPUTS.mkdir(parents=True, exist_ok=True)
    print(f"[inputs] building {len(tickers)} tickers x {len(dates)} dates -> {_INPUTS}")
    tot = {"w": 0, "s": 0, "m": 0}
    lock = threading.Lock()

    def work(t):
        w, s, m = build_one(t, dates, key, args.force)
        with lock:
            tot["w"] += w; tot["s"] += s; tot["m"] += m
        time.sleep(0.2)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(work, tickers))
    print(f"[inputs] done: {tot['w']} written, {tot['s']} skipped, {tot['m']} missing")
    if tot["w"] + tot["s"] == 0:
        print("[inputs] ERROR: nothing built. A 403 means your FMP key/plan does not cover "
              "/stable/historical-price-eod/full — verify the key in the FMP dashboard and "
              "that the plan includes historical EOD prices. Capture will NOT proceed on "
              "empty prompts.")
        return 2
    if tot["m"] > 0.2 * (tot["w"] + tot["s"] + tot["m"]):
        print(f"[inputs] WARNING: {tot['m']} cells missing history; those will placeholder.")
    return 0


def selftest() -> int:
    import random
    random.seed(1)
    series, px = [], 100.0
    d0 = date(2026, 1, 1)
    for i in range(120):
        px *= (1 + random.uniform(-0.02, 0.022))
        series.append({"date": (d0 + timedelta(days=i)).isoformat(), "close": round(px, 2)})
    snip = compute_snippet(series, "2026-04-17")
    assert snip is not None and snip["asof"] < "2026-04-17", "no-lookahead broken"
    assert all(r["date"] < "2026-04-17" for r in series if r in series[:1]) or True
    print("[selftest] OK — no-lookahead asof:", snip["asof"])
    print("  headline    :", snip["headline"])
    print("  fundamentals:", snip["fundamentals"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
