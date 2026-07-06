"""Shared cache + rate limiting: Redis in production, in-memory fallback.

If REDIS_URL is set (Railway injects it when a Redis service is attached)
and reachable, both features are backed by Redis so they survive restarts
and work across processes. Otherwise the previous in-process behaviour is
kept — fine for local dev and tests, where there is a single process.
"""

import json
import os
import time

_redis = None
if os.environ.get("REDIS_URL"):
    try:
        import redis as _redis_lib
        _redis = _redis_lib.Redis.from_url(
            os.environ["REDIS_URL"], decode_responses=True,
            socket_timeout=2, socket_connect_timeout=2)
        _redis.ping()
    except Exception:
        _redis = None  # unreachable — degrade to memory rather than crash

# --- in-memory fallbacks ---------------------------------------------------

_mem_kv: dict[str, tuple[float, str]] = {}   # key -> (expires_at|inf, json)
_mem_hits: dict[str, list[float]] = {}       # key -> hit timestamps


def backend() -> str:
    return "redis" if _redis is not None else "memory"


def reset():
    """Test hook: clear all in-memory state."""
    _mem_kv.clear()
    _mem_hits.clear()


# --- JSON key-value with TTL -------------------------------------------------

def get_json(key: str):
    if _redis is not None:
        try:
            raw = _redis.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None
    entry = _mem_kv.get(key)
    if entry is None or entry[0] < time.time():
        return None
    return json.loads(entry[1])


def set_json(key: str, value, ttl: int | None = None):
    raw = json.dumps(value)
    if _redis is not None:
        try:
            _redis.set(key, raw, ex=ttl)
        except Exception:
            pass
        return
    _mem_kv[key] = (time.time() + ttl if ttl else float("inf"), raw)


# --- rate limiting ---------------------------------------------------------

def rate_hit(key: str, limit: int, window: int) -> bool:
    """Record a hit; return True if still within the limit.

    Redis uses a fixed window (INCR + EXPIRE) — simple and multi-process
    safe. The memory fallback keeps the original sliding window.
    """
    if _redis is not None:
        try:
            n = _redis.incr(f"rl:{key}")
            if n == 1:
                _redis.expire(f"rl:{key}", window)
            return n <= limit
        except Exception:
            pass  # Redis hiccup — fall through to memory
    now = time.monotonic()
    hits = [t for t in _mem_hits.get(key, []) if now - t < window]
    if len(hits) >= limit:
        _mem_hits[key] = hits
        return False
    hits.append(now)
    _mem_hits[key] = hits
    if len(_mem_hits) > 10_000:  # bound memory under address churn
        _mem_hits.clear()
    return True
