# Tourist Companion System

Personalized Egypt trip planner: given a **budget and visitor type**, it selects the
optimal set of attractions. Originally a graduation project (Omar Reda, 193309) built
around a genetic algorithm; now evolving into a real application with a verified
dataset and an exact solver.

## Folder layout

| Folder | Contents |
|---|---|
| `data/places.csv` | **Canonical dataset** — 50 verified places (Giza, Cairo, Saqqara/Dahshur, Alexandria) with 4 price tiers, hours, coordinates, durations, sources. |
| `algorithm/solver.py` | Exact selection solver (OR-Tools CP-SAT) with category preference weights. |
| `algorithm/scheduler.py` | Day-by-day scheduling: geography, travel time, opening hours. |
| `algorithm/planner.py` | **End-to-end planner CLI** — selection + schedule. |
| `api/` | FastAPI service: planning, auth, saved trips; also serves the website. |
| `data/presets.json` | Curated trip programs shown on the homepage and Build page. |
| `tests/` | pytest suite: solver constraints, scheduler rules, full API flows. |
| `website/` | Tourist Companion website — home, Build, Login, My Trips (served by the API). |

Thesis-era material (report, SRS, presentations, source spreadsheets, and the
archived `experiments/` genetic-algorithm code) lives in the working folder but
is intentionally kept out of the repository for now.

## The dataset (`data/places.csv`)

One row per bookable ticket. Key columns:

- **4 price tiers** (EGP): `price_foreign_adult`, `price_foreign_student`,
  `price_egyptian_adult`, `price_egyptian_student`. Empty = that tier isn't sold.
- **`requires`** — ticket dependency (e.g. pyramid interiors require `giza-plateau`).
- **`excludes`** — mutually exclusive tickets (e.g. the Saqqara all-tombs combo vs.
  individual tomb tickets).
- **`visit_min`, `open`, `close`, `lat`, `lon`** — for future scheduling/routing.
- **`source`, `last_verified`, `needs_verification`** — provenance. Prices come from
  the [official Ministry list](https://mota.gov.eg/media/5a2ja2iu/ticket-english-5-11-2024-1.pdf)
  cross-checked against 2026 fee guides; rows marked `needs_verification=yes` are
  estimates for non-ministry sites (Cairo Tower, Bibliotheca, Sound & Light, Montaza).

Note: as of 2026 most ministry sites are **card-only** (no cash), and GEM foreign
tickets must be bought online at visit-gem.com. GEM foreign price rises to 1590 EGP
in Nov 2026.

## Running it

```bash
pip install -r requirements.txt

# Full app: website + API on http://localhost:8000 (Build Program page)
uvicorn main:app --app-dir api --port 8000

# CLI planner (day-by-day itinerary)
cd algorithm
python planner.py --budget 5000 --days 3
python planner.py --budget 2000 --days 2 --tier egyptian --student --prefer ancient=2

# Selection only (no scheduling)
python solver.py --budget 3000 --city Giza --hours 12
```

How it works:

1. **Selection** (`solver.py`, CP-SAT, exact): maximizes preference-weighted rating
   subject to budget, a trip-time cap, ticket dependencies (pyramid interiors need
   the plateau ticket), and combo exclusions. Optimality is proven, not approximated.
2. **Scheduling** (`scheduler.py`, heuristic): packs the selection into days —
   dependency clusters stay together, days never mix Cairo/Giza with Alexandria,
   and the packing simulates the clock (travel at city/highway speeds, waiting for
   opening, closing hours).
3. **Planner** (`planner.py`): runs 1→2, and re-solves with a tighter time cap if
   the schedule doesn't fit the requested days.

The thesis genetic-algorithm solver (archived under `experiments/`, not in this
repo) was approximate and modeled none of these constraints — it is superseded.

## API & accounts

The `api/` package is split by concern:

- `planning.py` — `POST /api/plan`, `GET /api/places`, `GET /api/presets`
- `auth.py` — `POST /api/auth/register|login|logout`, `GET /api/auth/me`.
  Passwords hashed with PBKDF2-SHA256 (600k iterations, stdlib); sessions are
  random tokens in an HttpOnly SameSite=Lax cookie, stored hashed in SQLite.
- `trips.py` — per-user saved trips (`POST/GET/DELETE /api/trips`)
- `db.py` — SQLite schema + per-request connection (`data/app.db`, created on
  startup; not committed)

The website pages `build.html`, `Login.html` and `mytrips.html` share
`css/app.css` and `js/auth.js`. The homepage's "top trips" cards deep-link into
the builder via `build.html?preset=<id>`; presets live in `data/presets.json`.

## Configuration

Settings are read from environment variables, loaded from a local `.env` if
present (copy `.env.example` to `.env`). Real environment variables always win,
so hosting platforms override the file. Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `TC_ENV` | `development` | `production` turns on secure (HTTPS-only) cookies |
| `TC_COOKIE_SECURE` | follows `TC_ENV` | force secure cookies on/off |
| `TC_SESSION_DAYS` | `30` | session cookie lifetime |
| `TC_DB_PATH` | `data/app.db` | SQLite file location |
| `PORT` | `8000` | port the server binds (hosts set this automatically) |

## Deploying (free) — Render.com

The app is a single process serving the API and the static site, so it deploys
as one web service. `render.yaml` and `Procfile` are already set up.

1. Push this repo to GitHub.
2. On [render.com](https://render.com) (free, no card): **New → Web Service**,
   connect the repo. Render reads `render.yaml` — build `pip install -r
   requirements.txt`, start `uvicorn main:app --app-dir api --host 0.0.0.0
   --port $PORT`, with `TC_ENV=production` (secure cookies on).
3. Deploy. You get a public `https://…onrender.com` URL.

Free-tier caveats: the service sleeps after ~15 min idle (first request then
takes ~30–50s to wake), and the disk is ephemeral — `data/app.db` resets on each
**redeploy** (not between requests). Fine for a live demo; for persistent user
data use Fly.io's free volume or Render's paid disk.

## Tests

```bash
python -m pytest
```

22 tests cover solver constraints (budget, dependencies, combo exclusions, tiers),
scheduler rules (same-day clusters, no Cairo/Alexandria mixing, opening hours),
and API flows (auth lifecycle, trip ownership, validation).

## Roadmap

1. ~~Clean, sourced dataset with dual pricing~~ ✔
2. ~~Exact selection solver~~ ✔
3. ~~Scheduling layer (days, travel time, opening hours)~~ ✔
4. ~~Category preference weights~~ ✔
5. ~~FastAPI service + website Build Program page~~ ✔
6. Verify the 4 estimated prices (Cairo Tower, Bibliotheca, Sound & Light, Montaza);
   expand dataset (Luxor/Aswan are already in the ministry list).
7. ~~Accounts, working login/register, saved trips~~ ✔
8. ~~Curated presets wired to the homepage~~ ✔
9. Real routing (Google Distance Matrix instead of haversine estimates), hotels as
   day anchors, multi-city trips with transfers.
10. Production hardening: HTTPS (set the session cookie `secure`), rate limiting
    on auth endpoints, backups for `data/app.db`.
