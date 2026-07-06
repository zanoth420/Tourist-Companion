"""Lock/exclude planning, share links, rates, and auth rate limiting."""

import pytest

import auth
import rates
from solver import DATA_FILE, load_places, solve


# --- solver lock / exclude -------------------------------------------------

def test_excluded_place_and_its_dependents_drop():
    places = load_places(DATA_FILE, "foreign", False, None)
    chosen, _ = solve(places, 50_000, excluded=["giza-plateau"])
    ids = {p["id"] for p in chosen}
    assert "giza-plateau" not in ids
    # anything requiring the plateau must be gone too
    assert not any(p["requires"].strip() == "giza-plateau" for p in chosen)


def test_locked_place_is_always_selected():
    places = load_places(DATA_FILE, "foreign", False, None)
    # tight budget where the expensive GEM wouldn't normally win
    baseline, _ = solve(places, 2000, max_minutes=400)
    assert "gem" not in {p["id"] for p in baseline}
    chosen, _ = solve(places, 2000, max_minutes=400, locked=["gem"])
    assert "gem" in {p["id"] for p in chosen}


def test_locking_unavailable_place_raises():
    places = load_places(DATA_FILE, "foreign", False, None)
    with pytest.raises(ValueError):
        solve(places, 5000, locked=["gem"], excluded=["gem"])


# --- plan endpoint extensions ----------------------------------------------

def test_plan_with_start_date_stamps_days(client):
    plan = client.post("/api/plan", json={
        "budget": 2000, "days": 2, "start_date": "2026-08-03"}).json()
    assert plan["days"][0]["date"] == "2026-08-03"
    if len(plan["days"]) > 1:
        assert plan["days"][1]["date"] == "2026-08-04"


def test_plan_exclude_via_api(client):
    plan = client.post("/api/plan", json={
        "budget": 3000, "days": 2, "excluded": ["egyptian-museum"]}).json()
    names = [s["id"] for d in plan["days"] for s in d["stops"]]
    assert "egyptian-museum" not in names


# --- share links -------------------------------------------------------------

def _saved_trip_id(client):
    plan = client.post("/api/plan", json={"budget": 1500, "days": 1}).json()
    return client.post("/api/trips", json={
        "name": "Share Me", "params": {"budget": 1500}, "plan": plan}).json()["id"]


def test_share_create_view_revoke(client, user):
    trip_id = _saved_trip_id(client)

    token = client.post(f"/api/trips/{trip_id}/share").json()["token"]
    # sharing twice returns the same token
    assert client.post(f"/api/trips/{trip_id}/share").json()["token"] == token

    # public view works without a session
    client.post("/api/auth/logout")
    shared = client.get(f"/api/shared/{token}")
    assert shared.status_code == 200
    assert shared.json()["name"] == "Share Me"
    assert "plan" in shared.json()

    # owner revokes -> link dies
    client.post("/api/auth/login",
                json={"email": "test@example.com", "password": "secret123"})
    assert client.delete(f"/api/trips/{trip_id}/share").status_code == 200
    assert client.get(f"/api/shared/{token}").status_code == 404


def test_share_requires_ownership(client, user):
    trip_id = _saved_trip_id(client)
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={
        "name": "Eve", "email": "eve2@example.com", "password": "secret123"})
    assert client.post(f"/api/trips/{trip_id}/share").status_code == 404


# --- rates -------------------------------------------------------------------

def test_rates_fallback_when_source_down(client, monkeypatch):
    monkeypatch.setattr(rates, "_fetch_live",
                        lambda: (_ for _ in ()).throw(OSError("down")))
    data = client.get("/api/rates").json()
    assert data["stale"] is True
    assert set(data["rates"]) == {"USD", "EUR", "GBP"}


def test_rates_served_from_cache(client):
    import cache
    cache.set_json(rates.FRESH_KEY, {"USD": 0.02, "EUR": 0.019, "GBP": 0.016}, 60)
    data = client.get("/api/rates").json()
    assert data["rates"]["USD"] == 0.02
    assert data["stale"] is False


def test_rates_expired_cache_marked_stale(client, monkeypatch):
    """Regression: an expired cache + failed refresh must report stale=True."""
    import cache
    cache.set_json(rates.LAST_KEY, {"USD": 0.02, "EUR": 0.019, "GBP": 0.016})
    monkeypatch.setattr(rates, "_fetch_live",
                        lambda: (_ for _ in ()).throw(OSError("down")))
    data = client.get("/api/rates").json()
    assert data["stale"] is True
    assert data["rates"]["USD"] == 0.02  # last-known rates, honestly flagged


# --- auth rate limiting --------------------------------------------------------

def test_login_rate_limited(client):
    body = {"email": "nobody@example.com", "password": "wrongpass1"}
    for _ in range(auth.RATE_LIMIT_ATTEMPTS):
        assert client.post("/api/auth/login", json=body).status_code == 401
    assert client.post("/api/auth/login", json=body).status_code == 429
