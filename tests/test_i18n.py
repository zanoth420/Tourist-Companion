"""Arabic place data is merged into the API responses (name_ar / area_ar)."""


def test_places_carry_arabic(client):
    rows = client.get("/api/places").json()
    assert any(r.get("name_ar") for r in rows)  # at least some translated


def test_plan_stops_carry_arabic(client):
    r = client.post("/api/plan", json={"budget": 2000, "days": 1, "cities": ["Cairo"]})
    assert r.status_code == 200
    stop = r.json()["days"][0]["stops"][0]
    assert stop.get("name_ar") and stop.get("area_ar")


def test_presets_carry_arabic(client):
    presets = client.get("/api/presets").json()
    assert all(p.get("name_ar") and p.get("description_ar") for p in presets)
