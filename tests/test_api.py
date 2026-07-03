"""End-to-end API tests: planning, auth flow, saved trips."""


def test_plan_endpoint(client):
    res = client.post("/api/plan", json={"budget": 2000, "days": 2})
    assert res.status_code == 200
    plan = res.json()
    assert plan["total_cost"] <= 2000
    assert len(plan["days"]) <= 2


def test_plan_rejects_bad_input(client):
    assert client.post("/api/plan", json={"budget": -5}).status_code == 422
    assert client.post("/api/plan", json={"budget": 100, "days": 99}).status_code == 422


def test_presets_and_places(client):
    presets = client.get("/api/presets").json()
    assert any(p["id"] == "pharaonic" for p in presets)
    places = client.get("/api/places").json()
    assert len(places) >= 40


# --- auth ----------------------------------------------------------------

def test_register_login_me_logout(client):
    reg = client.post("/api/auth/register", json={
        "name": "Omar", "email": "omar@example.com", "password": "secret123"})
    assert reg.status_code == 201

    me = client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["email"] == "omar@example.com"

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    login = client.post("/api/auth/login",
                        json={"email": "omar@example.com", "password": "secret123"})
    assert login.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_duplicate_email_rejected(client, user):
    res = client.post("/api/auth/register", json={
        "name": "Other", "email": "test@example.com", "password": "different1"})
    assert res.status_code == 409


def test_wrong_password_rejected(client, user):
    res = client.post("/api/auth/login",
                      json={"email": "test@example.com", "password": "wrongpass1"})
    assert res.status_code == 401


def test_weak_password_rejected(client):
    res = client.post("/api/auth/register", json={
        "name": "X", "email": "x@example.com", "password": "short"})
    assert res.status_code == 422


# --- trips -----------------------------------------------------------------

def _sample_trip(client):
    plan = client.post("/api/plan", json={"budget": 1500, "days": 1}).json()
    return {"name": "Test Trip", "params": {"budget": 1500, "days": 1}, "plan": plan}


def test_trips_require_login(client):
    assert client.get("/api/trips").status_code == 401


def test_save_list_get_delete_trip(client, user):
    trip_id = client.post("/api/trips", json=_sample_trip(client)).json()["id"]

    trips = client.get("/api/trips").json()
    assert len(trips) == 1 and trips[0]["name"] == "Test Trip"
    assert trips[0]["total_cost"] is not None

    full = client.get(f"/api/trips/{trip_id}").json()
    assert full["plan"]["days"]

    assert client.delete(f"/api/trips/{trip_id}").status_code == 200
    assert client.get("/api/trips").json() == []


def test_users_cannot_see_others_trips(client, user):
    trip_id = client.post("/api/trips", json=_sample_trip(client)).json()["id"]

    # second user
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={
        "name": "Eve", "email": "eve@example.com", "password": "secret123"})

    assert client.get(f"/api/trips/{trip_id}").status_code == 404
    assert client.delete(f"/api/trips/{trip_id}").status_code == 404
    assert client.get("/api/trips").json() == []
