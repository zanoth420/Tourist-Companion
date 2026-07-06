"""Shared paths and runtime settings for the API.

Settings come from environment variables, loaded from a local `.env` if one
exists (real environment variables always win, so hosting platforms like
Render override these). See `.env.example` for the full list.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")  # override=False: real env vars take precedence
except ImportError:
    pass  # python-dotenv is optional; plain env vars still work

SITE_DIR = ROOT / "website" / "Gradtouristcompanion"
PRESETS_FILE = ROOT / "data" / "presets.json"
PLACES_AR_FILE = ROOT / "data" / "places.ar.json"  # Arabic name/area per place id

# make the algorithm package importable (planner, solver, scheduler)
sys.path.insert(0, str(ROOT / "algorithm"))


def _bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


ENV = os.environ.get("TC_ENV", "development")
IS_PRODUCTION = ENV == "production"

SESSION_COOKIE = os.environ.get("TC_SESSION_COOKIE", "tc_session")
SESSION_DAYS = int(os.environ.get("TC_SESSION_DAYS", "30"))
# Secure cookies require HTTPS — on by default in production, off for local http.
COOKIE_SECURE = _bool("TC_COOKIE_SECURE", IS_PRODUCTION)

# Port is read by the start command ($PORT); kept here for reference/local use.
PORT = int(os.environ.get("PORT", "8000"))

# Public browser key for the Google Maps JavaScript API (the interactive trip
# map). It ships to the client, so it must be restricted by HTTP referrer in the
# Google Cloud console. Empty = the map feature quietly hides.
MAPS_API_KEY = os.environ.get("TC_MAPS_KEY", "")


def db_path() -> Path:
    """Resolved per call so tests can point at a temporary database."""
    return Path(os.environ.get("TC_DB_PATH", ROOT / "data" / "app.db"))
