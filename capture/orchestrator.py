"""Condition-based capture orchestrator. Captures one version of one migration
pair over a subgrid into an immutable data/raw/runs_<pair>_<version>.csv. The unit
is a single-model decision per (ticker, date, replicate). Seed policy cell_parity
derives the seed from (ticker,date,replicate) only, so v_old and v_new get
identical seeds at each cell and the version is the sole difference.

Parallel workers are throttled by a shared per-provider RPM limiter, with adaptive
retry/backoff for rate-limit and transient errors and a daily-quota circuit breaker
that defers a model's cells instead of hammering an exhausted bucket. A worst-case
cost reservation makes the spend cap safe under concurrency. Execution order does
NOT affect analysis (analysis is a pure, order-independent function of the CSV).

Usage:
  PILOT_MOCK=1 python orchestrator.py --pair openai_nano --version v_old --subgrid pilot
  python orchestrator.py --pair openai_nano --version v_old --subgrid full --concurrency 16
"""
from __future__ import annotations
import argparse, csv, hashlib, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

try:
    import resource
except ImportError:
    resource = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))

import agent as agentmod
import secrets as secretstore
import loader as C
import taskcfg

_HERE = Path(__file__).resolve().parent
_DATA = _HERE.parent / "data" / "raw"

CSV_FIELDS = [
    "pair", "version", "mode", "model_key", "api_model", "provider",
    "ticker", "date", "replicate", "attempt", "seed", "temperature",
    "timestamp_utc", "prompt_hash", "snippet_source", "snippet_asof",
    "direction", "conviction", "rationale",
    "input_tokens", "output_tokens", "cost_usd", "ok", "error", "raw_response",
]


def cell_parity_seed(master: int, ticker: str, d: str, replicate: int) -> int:
    raw = f"{master}|{ticker}|{d}|{replicate}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def price_of(mcfg, in_tok, out_tok) -> float:
    return (in_tok / 1e6) * mcfg.get("price_in", 0) + (out_tok / 1e6) * mcfg.get("price_out", 0)


def worst_case_cost(mcfg, est_in=60) -> float:
    return price_of(mcfg, est_in, int(mcfg.get("max_tokens", 2000)))


class RateLimiter:
    """Global min-interval limiter shared across worker threads for one provider."""
    def __init__(self, rpm):
        self.min_interval = (60.0 / rpm) if rpm and rpm > 0 else 0.0
        self.lock = threading.Lock()
        self.next_time = 0.0

    def acquire(self):
        if self.min_interval <= 0:
            return
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next_time)
            self.next_time = t + self.min_interval
            wait = t - now
        if wait > 0:
            time.sleep(wait)


def classify_error(err: str):
    e = err or ""
    el = e.lower()
    delay = None
    m = re.search(r"retrydelay['\":\s]+(\d+(?:\.\d+)?)s", el)
    if m:
        delay = float(m.group(1))
    if any(k in el for k in ("per_day", "perday", "requests_per_model_per_day",
                             "per-day", "requests_per_day")):
        return "daily_quota", delay
    if "resource_exhausted" in el and delay and delay > 300:
        return "daily_quota", delay
    if "429" in e or "rate limit" in el or "rate_limit" in el or "quota" in el \
            or "resource_exhausted" in el:
        return "rate_limit", delay
    if any(k in el for k in ("connection error", "timeout", "timed out",
                             "503", "unavailable", "502", "reset")):
        return "transient", delay
    return "other", delay


def load_done(path: Path) -> set:
    done = set()
    if path.exists():
        for r in csv.DictReader(path.open()):
            if r.get("ok") == "True":
                done.add((r["ticker"], r["date"], int(r["replicate"])))
    return done


def detect_mock(path: Path):
    if not path.exists():
        return None
    try:
        with path.open() as f:
            row = next(csv.DictReader(f))
        if row.get("mode"):
            return row["mode"].upper() == "MOCK"
        return "mock" in (row.get("rationale", "").lower())
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--version", required=True, choices=["v_old", "v_new"])
    ap.add_argument("--subgrid", default="minipilot")
    ap.add_argument("--spend-cap", type=float, default=None)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--inputs-dir", default=None)
    ap.add_argument("--temperature", type=float, default=None,
                    help="override decode temperature (robustness sweep)")
    ap.add_argument("--tag", default="",
                    help="suffix for the output CSV, e.g. _T07 (keeps a sweep separate)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = C.load_all()
    grid = cfg["grid"]
    master = int(grid["seed_master"])
    tickers, dates = C.subgrid(args.subgrid, cfg)
    cond = {c.version: c for c in C.conditions_for_pair(args.pair, cfg)}[args.version]
    mcfg = cond.model_cfg
    provider = mcfg["provider"]
    temp = args.temperature if args.temperature is not None else cond.temperature
    n_rep = cond.n_replicates
    cap = args.spend_cap if args.spend_cap is not None else float(grid["spend_cap_usd"])
    margin = float(grid["stop_margin_usd"])
    max_retries = int(grid.get("max_retries", 5))
    workers = max(1, args.concurrency or int(grid.get("concurrency", 1)))
    rpm_limits = grid.get("rpm_limits", {}) or {}
    daily_limits = grid.get("daily_limits", {}) or {}

    if args.inputs_dir:
        inputs_dir = Path(args.inputs_dir)
    else:
        own = _HERE.parent / taskcfg.DOC_DIR
        inputs_dir = own if (own.exists() and any(own.glob("*.json"))) else None

    mock = os.environ.get("PILOT_MOCK") == "1"
    mode = "MOCK" if mock else "REAL"
    _DATA.mkdir(parents=True, exist_ok=True)
    out_csv = _DATA / f"runs_{args.pair}_{args.version}{args.tag}.csv"

    if out_csv.exists():
        if not os.access(out_csv, os.W_OK):
            print(f"[capture] REFUSING: {out_csv.name} is read-only (frozen or synced). "
                  f"Run `make clean` (or chmod +w) first."); return 4
        prior_mock = detect_mock(out_csv)
        if prior_mock is not None and prior_mock != mock:
            print(f"[capture] REFUSING: {out_csv.name} holds "
                  f"{'MOCK' if prior_mock else 'REAL'} rows but this is a {mode} run. "
                  f"Run `make clean` first."); return 5

    calls = [(t, d, rep) for t in tickers for d in dates for rep in range(n_rep)]
    print(f"[capture] pair={args.pair} version={args.version} model={cond.model_key} "
          f"({mode}) subgrid={args.subgrid}")
    print(f"[capture] grid: {len(tickers)} tickers x {len(dates)} dates x {n_rep} reps "
          f"= {len(calls)} calls | T={temp} | seed_policy={cond.seed_policy}")
    print(f"[capture] concurrency: {workers} worker(s) | "
          f"rpm_limit[{provider}]={rpm_limits.get(provider, 'none')}")
    if inputs_dir is None and not mock:
        print("[capture] WARNING: no inputs/ dir found — using EMPTY placeholder prompts. "
              "Run capture/build_inputs.py first for a valid financial-context experiment.")

    est = worst_case_cost(mcfg) * len(calls)
    print(f"[capture] worst-case projected cost: ${est:.4f} (cap ${cap:.2f})")

    done = load_done(out_csv)
    todo = [c for c in calls if (c[0], c[1], int(c[2])) not in done]
    if done:
        print(f"[capture] resuming: {len(done)} cells done; {len(todo)} remaining.")
    if daily_limits.get(cond.model_key) and len(todo) > daily_limits[cond.model_key]:
        print(f"[capture] WARNING: {len(todo)} planned > daily_limit "
              f"{daily_limits[cond.model_key]}; over-quota cells will be deferred.")

    if args.dry_run:
        print("[capture] DRY RUN ok."); return 0
    if not mock:
        secretstore.get_key(provider)
    if resource is not None:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            resource.setrlimit(resource.RLIMIT_NOFILE, (min(max(soft, 8192), hard), hard))
        except Exception:
            pass

    limiter = RateLimiter(0 if mock else rpm_limits.get(provider, 0))
    new_file = not out_csv.exists()
    try:
        fh = out_csv.open("a", newline="")
    except PermissionError:
        print(f"[capture] REFUSING: cannot write {out_csv.name} (read-only). "
              f"Run `make clean` first."); return 4
    writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
    if new_file:
        writer.writeheader()

    st = {"cum": 0.0, "reserved": 0.0, "n_ok": 0, "n_fail": 0, "n_done": 0,
          "deferred": 0, "stop": False, "exhausted": False}
    lock_spend = threading.Lock()
    lock_io = threading.Lock()
    total = len(todo)

    def write_row(t, d, rep, seed, attempt, res):
        cost = price_of(mcfg, res.input_tokens, res.output_tokens)
        with lock_io:
            writer.writerow({
                "pair": args.pair, "version": args.version, "mode": mode,
                "model_key": cond.model_key, "api_model": mcfg["api_model"], "provider": provider,
                "ticker": t, "date": d, "replicate": rep, "attempt": attempt,
                "seed": seed, "temperature": temp,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "prompt_hash": res.prompt_hash, "snippet_source": res.snippet_source,
                "snippet_asof": res.snippet_asof,
                "direction": res.decision.direction if res.decision else "",
                "conviction": res.decision.conviction if res.decision else "",
                "rationale": res.decision.rationale if res.decision else "",
                "input_tokens": res.input_tokens, "output_tokens": res.output_tokens,
                "cost_usd": round(cost, 6), "ok": res.ok, "error": res.error or "",
                "raw_response": (res.raw_response or "").replace("\n", " ")[:2000],
            })
            fh.flush()
            st["n_done"] += 1
            st["n_ok" if res.ok else "n_fail"] += 1
            if st["n_done"] % 50 == 0 or st["n_done"] == total:
                pct = (100.0 * st["n_done"] / total) if total else 0.0
                print(f"  ...{st['n_done']}/{total} ({pct:.0f}%) done, ${st['cum']:.4f} spent")

    def process(slot):
        t, d, rep = slot
        seed = cell_parity_seed(master, t, d, rep)
        snip = agentmod.load_or_build_snippet(t, d, inputs_dir)
        wc = worst_case_cost(mcfg)
        with lock_spend:
            if st["stop"] or (st["cum"] + st["reserved"] + wc) > (cap - margin):
                st["stop"] = True; return
            st["reserved"] += wc
            deferred = st["exhausted"]
        try:
            if deferred:
                ph = agentmod.prompt_hash(agentmod.SYSTEM_PROMPT, agentmod.build_prompt(t, snip))
                res = agentmod.AgentResult(False, None, "", 0, 0,
                                           f"DEFERRED_DAILY_QUOTA: {cond.model_key}", ph,
                                           snip.source, snip.asof)
                with lock_io:
                    st["deferred"] += 1
                write_row(t, d, rep, seed, 1, res)
                return
            for attempt in range(1, max_retries + 2):
                limiter.acquire()
                res = agentmod.run_agent(mcfg, t, snip, temp, seed)
                with lock_spend:
                    st["cum"] += price_of(mcfg, res.input_tokens, res.output_tokens)
                if res.ok:
                    write_row(t, d, rep, seed, attempt, res)
                    return
                kind, delay = classify_error(res.error)
                if kind == "daily_quota":
                    with lock_spend:
                        st["exhausted"] = True
                    res.error = f"DEFERRED_DAILY_QUOTA: {cond.model_key} ({res.error})"
                    with lock_io:
                        st["deferred"] += 1
                    write_row(t, d, rep, seed, attempt, res)
                    return
                if kind in ("rate_limit", "transient") and attempt <= max_retries:
                    time.sleep(min(30.0, (delay or 3.0) if kind == "rate_limit"
                                   else 0.4 * (2 ** (attempt - 1))))
                    continue
                write_row(t, d, rep, seed, attempt, res)
                with lock_io:
                    print(f"  ! {t} {d} r{rep} attempt {attempt} FAILED: {res.error}")
                return
        finally:
            with lock_spend:
                st["reserved"] -= wc

    try:
        if workers == 1:
            for slot in todo:
                if st["stop"]:
                    break
                process(slot)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                list(ex.map(process, todo))
    finally:
        fh.close()

    if st["stop"]:
        print(f"[capture] STOP: spend cap ${cap:.2f} guard tripped (resume by re-running).")
    if st["exhausted"]:
        print(f"[capture] daily quota hit for {cond.model_key}; {st['deferred']} cells DEFERRED.")
    print(f"[capture] done: {st['n_ok']} ok, {st['n_fail']} failed "
          f"({st['deferred']} deferred), spend ${st['cum']:.4f} -> {out_csv}")
    print(f"[capture] next: python capture/freeze.py --pair {args.pair} --version {args.version}")
    # exit 3 = INCOMPLETE (cells deferred by a daily-quota breaker); the CSV is left
    # writable so it can be backfilled after the quota resets. Do NOT freeze it.
    return 3 if st["deferred"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
