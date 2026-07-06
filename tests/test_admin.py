"""Admin API: TC_ADMIN_EMAILS promotion, access control, stats, user delete."""

import pytest


@pytest.fixture()
def admin(client, monkeypatch):
    """A registered, logged-in admin (email listed in TC_ADMIN_EMAILS)."""
    monkeypatch.setenv("TC_ADMIN_EMAILS", "boss@example.com")
    res = client.post("/api/auth/register", json={
        "name": "Boss", "email": "boss@example.com", "password": "secret123"})
    assert res.status_code == 201 and res.json()["is_admin"] is True
    return res.json()


def test_admin_requires_login(client):
    assert client.get("/api/admin/stats").status_code == 401


def test_admin_forbidden_for_normal_user(client, user):
    assert client.get("/api/admin/stats").status_code == 403


def test_email_is_normalized_to_lowercase(client):
    client.post("/api/auth/register", json={
        "name": "A", "email": "Mixed@Example.COM", "password": "secret123"})
    res = client.post("/api/auth/login",
                      json={"email": "mixed@example.com", "password": "secret123"})
    assert res.status_code == 200
    assert res.json()["email"] == "mixed@example.com"


def test_admin_stats_and_users(client, admin):
    stats = client.get("/api/admin/stats").json()
    assert stats["users"] == 1 and stats["trips"] == 0
    assert stats["recent_users"][0]["email"] == "boss@example.com"
    users = client.get("/api/admin/users").json()
    assert users[0]["is_admin"]


def test_admin_cannot_delete_self(client, admin):
    assert client.delete(f"/api/admin/users/{admin['id']}").status_code == 400


def test_admin_deletes_user_and_their_trips(client, admin, monkeypatch):
    # a second (normal) user saves a trip...
    client.post("/api/auth/register", json={
        "name": "Victim", "email": "victim@example.com", "password": "secret123"})
    plan = client.post("/api/plan", json={"budget": 1500, "days": 1,
                                          "cities": ["Cairo"]}).json()
    client.post("/api/trips", json={"name": "t", "params": {}, "plan": plan})
    # ...then the admin logs back in and removes them
    client.post("/api/auth/login",
                json={"email": "boss@example.com", "password": "secret123"})
    users = client.get("/api/admin/users").json()
    victim = next(u for u in users if u["email"] == "victim@example.com")
    assert victim["trips"] == 1
    assert client.delete(f"/api/admin/users/{victim['id']}").json()["ok"] is True
    stats = client.get("/api/admin/stats").json()
    assert stats["users"] == 1 and stats["trips"] == 0  # cascade removed the trip
