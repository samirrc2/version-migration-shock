"""Central secrets loader. `from secrets import get_key`. Walks up from this file
to find an "API Keys" folder (or a keys file alongside). Environment variables win
over the file."""
from __future__ import annotations
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent

_KEY_FILENAMES = ("keys.env", "keys.env.txt", "keys.txt")


def _resolve_keys_file() -> Path:
    override = os.environ.get("KEYS_ENV_PATH")
    if override:
        return Path(override).expanduser()
    for base in [_HERE, *_HERE.parents][:6]:
        for d in (base / "API Keys", base):
            for fn in _KEY_FILENAMES:
                c = d / fn
                if c.exists():
                    return c
    return _HERE / "keys.env"


_KEYS_FILE = _resolve_keys_file()

_PROVIDER_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


_FILE_CACHE = _parse_env_file(_KEYS_FILE)


def get_raw(var_name: str) -> str | None:
    return (os.environ.get(var_name) or _FILE_CACHE.get(var_name)) or None


def get_key(provider: str) -> str:
    provider = provider.lower()
    if provider not in _PROVIDER_ENV:
        raise KeyError(f"Unknown provider {provider!r}. Known: {sorted(set(_PROVIDER_ENV))}")
    var = _PROVIDER_ENV[provider]
    val = get_raw(var)
    if not val:
        raise RuntimeError(
            f"No API key for provider {provider!r}. Expected {var} in {_KEYS_FILE} "
            f"or the environment.")
    return val


def get_base_url(provider: str) -> str | None:
    if provider.lower() == "anthropic":
        return get_raw("ANTHROPIC_BASE_URL")
    return None


if __name__ == "__main__":
    print(f"keys file: {_KEYS_FILE}  present={_KEYS_FILE.exists()}")
    for prov, var in sorted(set(_PROVIDER_ENV.items())):
        print(f"  {prov:10s} <- {var:18s} : {'FOUND' if get_raw(var) else 'missing'}")
