"""The trip-map feature: a public config endpoint and coordinates on every stop."""


def test_config_endpoint_exposes_maps_key(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    assert "maps_key" in r.json()  # empty by default; set via TC_MAPS_KEY


def test_plan_stops_carry_coordinates(client):
    r = client.post("/api/plan", json={"budget": 2000, "days": 1, "cities": ["Cairo"]})
    assert r.status_code == 200
    stop = r.json()["days"][0]["stops"][0]
    assert isinstance(stop["lat"], float) and isinstance(stop["lon"], float)
    assert 22 < stop["lat"] < 32 and 24 < stop["lon"] < 36  # inside Egypt's bounds
