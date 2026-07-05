"""Exchange rates for the currency toggle (EGP -> USD/EUR/GBP).

Fetched from the free, key-less open.er-api.com endpoint and cached in
memory for 12 hours. If the fetch fails (offline, rate-limited), a static
fallback is served with `stale: true` so the UI can hint the rate is
approximate. Display-only — all money in the system stays in EGP.
"""

import time
import urllib.request
import json

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["rates"])

CURRENCIES = ("USD", "EUR", "GBP")
CACHE_TTL = 12 * 3600
SOURCE_URL = "https://open.er-api.com/v6/latest/EGP"

# Approximate fallback (July 2026); only used when the live fetch fails.
FALLBACK = {"USD": 0.021, "EUR": 0.018, "GBP": 0.015}

_cache = {"rates": None, "fetched_at": 0.0}


def _fetch_live():
    with urllib.request.urlopen(SOURCE_URL, timeout=5) as resp:
        data = json.load(resp)
    if data.get("result") != "success":
        raise ValueError("rate source returned an error")
    return {c: data["rates"][c] for c in CURRENCIES}


@router.get("/rates")
def get_rates():
    now = time.time()
    if _cache["rates"] is None or now - _cache["fetched_at"] > CACHE_TTL:
        try:
            _cache["rates"] = _fetch_live()
            _cache["fetched_at"] = now
        except Exception:
            if _cache["rates"] is None:  # nothing cached yet — use fallback
                return {"base": "EGP", "rates": FALLBACK, "stale": True}
            # keep serving the stale cache, retry next request
    return {"base": "EGP", "rates": _cache["rates"], "stale": False}
