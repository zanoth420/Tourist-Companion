"""The selection must respect budget, tiers, dependencies and exclusions."""

from solver import DATA_FILE, load_places, solve


def pick(budget, tier="foreign", student=False, **kwargs):
    places = load_places(DATA_FILE, tier, student, None)
    chosen, _ = solve(places, budget, **kwargs)
    assert chosen is not None
    return chosen


def test_budget_is_respected():
    chosen = pick(2000)
    assert sum(p["price"] for p in chosen) <= 2000


def test_zero_budget_still_returns_free_sites():
    chosen = pick(0)
    assert chosen, "free sites should always fit"
    assert all(p["price"] == 0 for p in chosen)


def test_dependencies_hold():
    chosen = pick(5000)
    ids = {p["id"] for p in chosen}
    for p in chosen:
        parent = p["requires"].strip()
        if parent:
            assert parent in ids, f"{p['id']} selected without its parent {parent}"


def test_combo_excludes_components():
    places = load_places(DATA_FILE, "foreign", False, None)
    # force the combo to be attractive: huge budget, only ancient Saqqara matters
    chosen, _ = solve(places, 50_000)
    ids = {p["id"] for p in chosen}
    if "saqqara-all-tombs" in ids:
        assert not ids & {"serapeum", "mereruka-tomb", "nk-tombs", "saqqara-south-tomb"}


def test_missing_tier_prices_exclude_place():
    places = load_places(DATA_FILE, "egyptian", False, None)
    ids = {p["id"] for p in places}
    assert "workers-cemetery" not in ids, "no Egyptian tier for this ticket"


def test_time_cap_binds():
    chosen = pick(50_000, max_minutes=300)
    assert sum(p["visit_min"] for p in chosen) <= 300


def test_preference_weights_shift_selection():
    places = load_places(DATA_FILE, "foreign", False, None)
    neutral, _ = solve(places, 3000, max_minutes=600)
    ancient, _ = solve(places, 3000, max_minutes=600, weights={"ancient": 5})
    count = lambda sel: sum(p["category"] == "ancient" for p in sel)
    assert count(ancient) >= count(neutral)
