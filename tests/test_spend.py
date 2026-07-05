"""The spend preference must trade cost against rating monotonically."""

from solver import DATA_FILE, load_places, solve


def _cost(spend):
    places = load_places(DATA_FILE, "foreign", False, ["Cairo"])
    chosen, _ = solve(places, 3000, max_minutes=900, spend=spend)
    return sum(p["price"] for p in chosen)


def test_spend_modes_order_by_cost():
    value, balanced, premium = _cost("value"), _cost("balanced"), _cost("premium")
    assert value <= balanced <= premium
    assert value < premium  # the two extremes must actually differ


def test_unknown_spend_falls_back_to_balanced():
    places = load_places(DATA_FILE, "foreign", False, ["Cairo"])
    a, _ = solve(places, 3000, max_minutes=900, spend="nonsense")
    b, _ = solve(places, 3000, max_minutes=900, spend="balanced")
    assert sum(p["price"] for p in a) == sum(p["price"] for p in b)


def test_spend_via_api(client):
    base = {"budget": 3000, "days": 2, "cities": ["Cairo"]}
    costs = {m: client.post("/api/plan", json={**base, "spend": m}).json()["total_cost"]
             for m in ("value", "balanced", "premium")}
    assert costs["value"] <= costs["balanced"] <= costs["premium"]


def test_bad_spend_rejected(client):
    assert client.post("/api/plan", json={"budget": 2000, "spend": "cheap"}).status_code == 422
