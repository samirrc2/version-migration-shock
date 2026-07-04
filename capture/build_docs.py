"""Build fundamentals documents into docs/<TICKER>_<DATE>.json for the credit-health
and earnings tasks. For each (ticker, analysis_date) cell, select the most recent
quarterly filing with filingDate strictly BEFORE the analysis date (no lookahead),
and write: a human-readable financial summary (what the model sees) plus a hidden
`fin` block of the raw figures used to compute the objective ground truth.

Immutable source (reported 10-Q financials never change) -> reproducible when frozen.
One income + one balance fetch per ticker, from FMP stable REST. Needs FMP_API_KEY.
  python capture/build_docs.py --subgrid full
  python capture/build_docs.py --selftest
"""
from __future__ import annotations
import argparse, json, sys, time, threading
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import secrets as secretstore
import loader as C

_DOCS = Path(__file__).resolve().parent.parent / "docs"
_BASE = "https://financialmodelingprep.com/stable/{ep}?symbol={t}&period=quarter&limit=40&apikey={k}"


def _get(ep, ticker, key, retries=4):
    url = _BASE.format(ep=ep, t=ticker, k=key)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper2/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())
            return d if isinstance(d, list) else d.get("data", d) if isinstance(d, dict) else []
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (2 ** attempt)); continue
            raise
        except Exception as e:
            last = e; time.sleep(1.0 * (2 ** attempt)); continue
    raise last or RuntimeError("fetch failed")


def _g(d, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def make_doc(inc: dict, bal: dict, analysis_date: str) -> dict:
    filing = (inc.get("filingDate") or "")[:10]
    period = f"{inc.get('fiscalYear','')} {inc.get('period','')}".strip()
    rev = _num(_g(inc, "revenue"))
    gp = _num(_g(inc, "grossProfit"))
    opinc = _num(_g(inc, "operatingIncome", "ebit"))
    ni = _num(_g(inc, "netIncome", "bottomLineNetIncome"))
    eps = _num(_g(inc, "epsDiluted", "eps"))
    ta = _num(_g(bal, "totalAssets"))
    tl = _num(_g(bal, "totalLiabilities"))
    eq = _num(_g(bal, "totalStockholdersEquity", "totalEquity"))
    tca = _num(_g(bal, "totalCurrentAssets"))
    tcl = _num(_g(bal, "totalCurrentLiabilities"))
    re_ = _num(_g(bal, "retainedEarnings"))
    gm = (gp / rev * 100) if (gp is not None and rev) else None
    opm = (opinc / rev * 100) if (opinc is not None and rev) else None
    curr = (tca / tcl) if (tca is not None and tcl) else None

    def m(x):
        return "n/a" if x is None else f"{x/1e6:,.0f}"

    text = (f"Fiscal period {period} (filed {filing}). "
            f"Revenue {m(rev)}M, gross margin {'n/a' if gm is None else f'{gm:.0f}%'}, "
            f"operating income {m(opinc)}M (operating margin {'n/a' if opm is None else f'{opm:.0f}%'}), "
            f"net income {m(ni)}M, diluted EPS {'n/a' if eps is None else eps}. "
            f"Total assets {m(ta)}M, total liabilities {m(tl)}M, shareholders' equity {m(eq)}M. "
            f"Current assets {m(tca)}M vs current liabilities {m(tcl)}M "
            f"(current ratio {'n/a' if curr is None else f'{curr:.2f}'}), "
            f"retained earnings {m(re_)}M.")
    return {
        "asof": filing, "period": period, "text": text,
        "fin": {"revenue": rev, "ebit": opinc, "total_assets": ta, "total_liabilities": tl,
                "equity": eq, "current_assets": tca, "current_liabilities": tcl,
                "retained_earnings": re_},
        "source_provenance": "fmp_reported_quarterly",
    }


def build_one(ticker, dates, key, force):
    need = [d for d in dates if force or not (_DOCS / f"{ticker}_{d}.json").exists()]
    if not need:
        return 0, len(dates), 0
    try:
        inc = _get("income-statement", ticker, key)
        bal = _get("balance-sheet-statement", ticker, key)
    except Exception as e:
        print(f"  ! {ticker}: fetch failed: {type(e).__name__}: {str(e)[:90]}")
        return 0, 0, len(need)
    bal_by = {(b.get("fiscalYear"), b.get("period")): b for b in bal}
    inc_sorted = sorted([r for r in inc if r.get("filingDate")], key=lambda r: r["filingDate"])
    w = s = miss = 0
    for d in dates:
        f = _DOCS / f"{ticker}_{d}.json"
        if not force and f.exists():
            s += 1; continue
        # latest filing STRICTLY before the analysis date
        elig = [r for r in inc_sorted if r["filingDate"][:10] < d]
        if not elig:
            miss += 1; continue
        inc_r = elig[-1]
        bal_r = bal_by.get((inc_r.get("fiscalYear"), inc_r.get("period")), {})
        f.write_text(json.dumps(make_doc(inc_r, bal_r, d), indent=2))
        w += 1
    return w, s, miss


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
        print("[docs] ERROR: FMP_API_KEY not found"); return 2
    tickers, dates = C.subgrid(args.subgrid)
    _DOCS.mkdir(parents=True, exist_ok=True)
    print(f"[docs] building {len(tickers)} tickers x {len(dates)} dates -> {_DOCS}")
    tot = {"w": 0, "s": 0, "m": 0}
    lock = threading.Lock()

    def work(t):
        w, s, m = build_one(t, dates, key, args.force)
        with lock:
            tot["w"] += w; tot["s"] += s; tot["m"] += m
        time.sleep(0.2)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(work, tickers))
    print(f"[docs] done: {tot['w']} written, {tot['s']} skipped, {tot['m']} missing")
    if tot["w"] + tot["s"] == 0:
        print("[docs] ERROR: nothing built. Check FMP_API_KEY / plan access to "
              "/stable/income-statement and /stable/balance-sheet-statement.")
        return 2
    return 0


def selftest() -> int:
    inc = {"fiscalYear": "2026", "period": "Q1", "filingDate": "2026-01-30",
           "revenue": 143756e6, "grossProfit": 69231e6, "operatingIncome": 50852e6,
           "netIncome": 42097e6, "epsDiluted": 2.84}
    bal = {"fiscalYear": "2026", "period": "Q1", "totalAssets": 371082e6,
           "totalLiabilities": 264591e6, "totalStockholdersEquity": 106491e6,
           "totalCurrentAssets": 145000e6, "totalCurrentLiabilities": 135520e6,
           "retainedEarnings": 12359e6}
    doc = make_doc(inc, bal, "2026-02-06")
    assert doc["asof"] < "2026-02-06", "no-lookahead broken"
    print("[selftest] OK asof:", doc["asof"])
    print("  text:", doc["text"])
    print("  fin :", doc["fin"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
