"""Single decision generator: build a no-lookahead prompt, call one model version,
return STRICT JSON. Includes a version-aware offline mock (PILOT_MOCK=1) that
simulates a vendor moving the decision boundary between v_old and v_new, so the
migration pipeline runs end-to-end with no network and no spend."""
from __future__ import annotations
import json
import re
import os
import sys
import hashlib
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import secrets as secretstore
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import taskcfg

_HERE = Path(__file__).resolve().parent
_PROMPT = (_HERE.parent / taskcfg.PROMPT_FILE)

VALID_DIRECTIONS = taskcfg.CATEGORY_SET
CATEGORIES = taskcfg.CATEGORIES

_CLIENTS: dict[str, Any] = {}
_CLIENTS_LOCK = threading.Lock()


def _load_prompt_template():
    txt = _PROMPT.read_text()
    sys_part = txt.split("[SYSTEM]", 1)[1].split("[USER]", 1)[0].strip()
    usr_part = txt.split("[USER]", 1)[1].strip()
    return sys_part, usr_part


SYSTEM_PROMPT, USER_TEMPLATE = _load_prompt_template()


@dataclass
class Snippet:
    text: str
    asof: str
    source: str


def _day_before(iso: str) -> str:
    return (date.fromisoformat(iso) - timedelta(days=1)).isoformat()


def load_or_build_snippet(ticker: str, analysis_date: str, inputs_dir: Path | None) -> Snippet:
    if inputs_dir is not None:
        f = Path(inputs_dir) / f"{ticker}_{analysis_date}.json"
        if f.exists():
            d = json.loads(f.read_text())
            asof = d.get("asof") or _day_before(analysis_date)
            if date.fromisoformat(asof) >= date.fromisoformat(analysis_date):
                raise ValueError(f"LOOKAHEAD: {ticker} asof {asof} !< {analysis_date}")
            if d.get("text"):
                text = str(d["text"]).strip()
            else:
                text = (f"Headline: {d.get('headline','').strip()}\n"
                        f"Fundamentals: {d.get('fundamentals','').strip()}")
            return Snippet(text.strip(), asof, "inputs_file")
    asof = _day_before(analysis_date)
    text = (f"No curated snippet supplied for {ticker}. Only public information "
            f"available on or before {asof} may be used. Base the call on prior "
            f"knowledge of the company as of {asof}.")
    return Snippet(text, asof, "constructed_placeholder")


def build_prompt(ticker: str, snippet: Snippet) -> str:
    return USER_TEMPLATE.format(asof=snippet.asof, ticker=ticker, snippet=snippet.text)


def prompt_hash(system: str, user: str) -> str:
    return hashlib.sha256((system + "\n\x1e\n" + user).encode()).hexdigest()[:16]


@dataclass
class Decision:
    direction: str
    conviction: int
    rationale: str


def parse_strict(raw: str) -> Decision:
    txt = raw.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", txt.strip())
    start = txt.find("{")
    if start == -1:
        raise ValueError(f"No JSON object in response: {raw[:200]!r}")
    obj, _ = json.JSONDecoder().raw_decode(txt[start:])
    direction = str(obj["direction"]).strip().upper()
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"direction {direction!r} invalid")
    conviction = int(obj["conviction"])
    if not (1 <= conviction <= 5):
        raise ValueError(f"conviction {conviction} out of range")
    rationale = " ".join(str(obj["rationale"]).split()[:30])
    return Decision(direction, conviction, rationale)


@dataclass
class AgentResult:
    ok: bool
    decision: Decision | None
    raw_response: str
    input_tokens: int
    output_tokens: int
    error: str | None
    prompt_hash: str
    snippet_source: str = ""
    snippet_asof: str = ""


def _u01(s: str) -> float:
    return (int(hashlib.sha256(s.encode()).hexdigest()[:12], 16) / 0xFFFFFFFFFFFF)


def _mock_call(model_cfg, ticker, snippet, seed):
    """Simulate one model version's decision. Latent cell signal s0 is shared by
    both versions; replicate jitter eps depends only on the seed (identical across
    versions at a matched cell/replicate), so cross-version flips come from the
    version's boundary shift, and within-version flips come from eps across
    replicates (the noise floor)."""
    s0 = 2.0 * _u01(f"signal|{ticker}|{snippet.asof}") - 1.0
    eps = (2.0 * _u01(f"jitter|{seed}") - 1.0) * 0.06
    shift = float(model_cfg.get("mock_signal_shift", 0.0))
    hw = float(model_cfg.get("mock_hold_halfwidth", 0.33))
    cbias = int(model_cfg.get("mock_conviction_bias", 0))

    eff = s0 + eps + shift
    idx = 0 if eff > hw else (2 if eff < -hw else 1)
    direction = CATEGORIES[idx]
    dist = abs(eff) - hw if idx != 1 else hw - abs(eff)
    conviction = max(1, min(5, 1 + int(round(4 * min(1.0, abs(dist) / 0.6))) + cbias))
    raw = json.dumps({"direction": direction, "conviction": conviction,
                      "rationale": "mock deterministic version-aware response"})
    return raw, 40, 12


def _client(kind: str):
    with _CLIENTS_LOCK:
        c = _CLIENTS.get(kind)
        if c is not None:
            return c
        if kind == "openai":
            from openai import OpenAI
            c = OpenAI(api_key=secretstore.get_key("openai"), max_retries=0)
        elif kind == "xai":
            from openai import OpenAI
            c = OpenAI(api_key=secretstore.get_key("xai"),
                       base_url="https://api.x.ai/v1", max_retries=0)
        elif kind == "anthropic":
            from anthropic import Anthropic
            kwargs = {"api_key": secretstore.get_key("anthropic")}
            base = secretstore.get_base_url("anthropic")
            if base:
                kwargs["base_url"] = base
            c = Anthropic(**kwargs)
        elif kind == "gemini":
            from google import genai
            c = genai.Client(api_key=secretstore.get_key("google"))
        else:
            raise ValueError(f"unknown client {kind}")
        _CLIENTS[kind] = c
        return c


def _openai_compatible(client, mcfg, system, user, temperature, seed):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    base = {"model": mcfg["api_model"], "messages": msgs,
            "response_format": {"type": "json_object"}}
    if seed is not None:
        base["seed"] = seed
    if mcfg.get("reasoning_effort"):
        base["reasoning_effort"] = mcfg["reasoning_effort"]
    max_out = int(mcfg.get("max_tokens", 2000))
    last = None
    for tok_param, with_temp in (("max_completion_tokens", True),
                                 ("max_completion_tokens", False),
                                 ("max_tokens", True)):
        kwargs = dict(base)
        kwargs[tok_param] = max_out
        if with_temp:
            kwargs["temperature"] = temperature
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:
            last = e
            m = str(e).lower()
            if "response_format" in m:
                base.pop("response_format", None); continue
            if "reasoning_effort" in m:
                base.pop("reasoning_effort", None); continue
            if any(k in m for k in ("temperature", "max_tokens", "max_completion",
                                    "unsupported", "unknown parameter")):
                continue
            raise
        u = resp.usage
        content = resp.choices[0].message.content or ""
        if content.strip():
            return content, u.prompt_tokens, u.completion_tokens
        last = RuntimeError(f"empty content (finish={resp.choices[0].finish_reason}, "
                            f"ctok={getattr(u, 'completion_tokens', None)}) — try raising "
                            f"the token budget or lowering reasoning effort")
    raise last or RuntimeError("all openai-compatible signatures failed")


def _call_gemini(mcfg, system, user, temperature, seed):
    from google.genai import types
    client = _client("gemini")
    gc = {"system_instruction": system, "temperature": temperature,
          "max_output_tokens": int(mcfg.get("max_tokens", 256)),
          "response_mime_type": "application/json"}
    try:
        gc["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    except Exception:
        pass
    if seed is not None:
        gc["seed"] = seed
    resp = client.models.generate_content(model=mcfg["api_model"], contents=user,
                                           config=types.GenerateContentConfig(**gc))
    um = resp.usage_metadata
    return resp.text or "", um.prompt_token_count, (um.candidates_token_count or 0)


def _call_anthropic(mcfg, system, user, temperature, seed):
    client = _client("anthropic")
    resp = client.messages.create(model=mcfg["api_model"],
        max_tokens=int(mcfg.get("max_tokens", 256)), temperature=temperature,
        system=system, messages=[{"role": "user", "content": user}])
    text = "".join(getattr(b, "text", "") for b in resp.content)
    return text, resp.usage.input_tokens, resp.usage.output_tokens


def call_model(mcfg, system, user, temperature, seed):
    provider = mcfg["provider"]
    if provider == "openai":
        return _openai_compatible(_client("openai"), mcfg, system, user, temperature, seed)
    if provider == "xai":
        return _openai_compatible(_client("xai"), mcfg, system, user, temperature, seed)
    if provider in ("google", "gemini"):
        return _call_gemini(mcfg, system, user, temperature, seed)
    if provider == "anthropic":
        return _call_anthropic(mcfg, system, user, temperature, seed)
    raise ValueError(f"unknown provider {provider!r}")


def run_agent(model_cfg, ticker, snippet: Snippet, temperature: float, seed: int) -> AgentResult:
    user = build_prompt(ticker, snippet)
    ph = prompt_hash(SYSTEM_PROMPT, user)
    src, asof = snippet.source, snippet.asof
    try:
        if os.environ.get("PILOT_MOCK") == "1":
            raw, in_tok, out_tok = _mock_call(model_cfg, ticker, snippet, seed)
        else:
            raw, in_tok, out_tok = call_model(model_cfg, SYSTEM_PROMPT, user, temperature, seed)
    except Exception as e:
        return AgentResult(False, None, "", 0, 0, f"{type(e).__name__}: {e}", ph, src, asof)
    try:
        dec = parse_strict(raw)
    except Exception as e:
        return AgentResult(False, None, raw, in_tok, out_tok, f"parse: {e}", ph, src, asof)
    return AgentResult(True, dec, raw, in_tok, out_tok, None, ph, src, asof)
