"""Exchange rates for the currency toggle (EGP -> USD/EUR/GBP).

Fetched from the free, key-less open.er-api.com endpoint and cached for
12 hours (Redis when available, in-memory otherwise). If a refresh fails,
the last known rates are served with `stale: true` — previously this case
wrongly reported stale rates as fresh. Display-only — all money in the
system stays in EGP.
"""

import urllib.request
import json

from fastapi import APIRouter

import cache

router = APIRouter(prefix="/api", tags=["rates"])

CURRENCIES = ("USD", "EUR", "GBP")
CACHE_TTL = 12 * 3600
SOURCE_URL = "https://open.er-api.com/v6/latest/EGP"

FRESH_KEY = "rates:fresh"   # expires after CACHE_TTL
LAST_KEY = "rates:last"     # never expires; stale fallback

# Approximate fallback (July 2026); only used when nothing was ever fetched.
FALLBACK = {"USD": 0.021, "EUR": 0.018, "GBP": 0.015}


def _fetch_live():
    with urllib.request.urlopen(SOURCE_URL, timeout=5) as resp:
        data = json.load(resp)
    if data.get("result") != "success":
        raise ValueError("rate source returned an error")
    return {c: data["rates"][c] for c in CURRENCIES}


@router.get("/rates")
def get_rates():
    rates = cache.get_json(FRESH_KEY)
    if rates is not None:
        return {"base": "EGP", "rates": rates, "stale": False}
    try:
        rates = _fetch_live()
        cache.set_json(FRESH_KEY, rates, CACHE_TTL)
        cache.set_json(LAST_KEY, rates)
        return {"base": "EGP", "rates": rates, "stale": False}
    except Exception:
        last = cache.get_json(LAST_KEY)
        return {"base": "EGP", "rates": last or FALLBACK, "stale": True}
