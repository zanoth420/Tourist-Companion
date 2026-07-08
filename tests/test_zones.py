"""Regression: the selection must be geographically coherent.

The original bug: boosting "nature" with no city filter produced one short
stop per day scattered across half of Egypt (Ain Sokhna sulfur springs
alone, one Hurghada mosque alone, then a day of Cairo churches).
"""

from planner import plan
from regions import zone
from solver import DATA_FILE, load_places


def _scenario():
    return plan(budget=3000, days=3, weights={"nature": 2})


def test_at_most_one_region_per_day():
    result = _scenario()
    zones = {zone(s["place"]) for d in result["days"] for s in d["stops"]}
    assert len(zones) <= 3


def test_interest_boost_focuses_the_trip():
    result = _scenario()
    stops = [s["place"] for d in result["days"] for s in d["stops"]]
    nature = sum(p["category"] == "nature" for p in stops)
    assert nature / len(stops) >= 0.5, "a nature trip must be mostly nature"


def test_visited_regions_are_worth_the_trip():
    """Each visited region contributes a real chunk of a day (or all it has)."""
    result = _scenario()
    all_places = load_places(DATA_FILE, "foreign", False, None)
    by_zone: dict[str, int] = {}
    for d in result["days"]:
        for s in d["stops"]:
            z = zone(s["place"])
            by_zone[z] = by_zone.get(z, 0) + s["place"]["visit_min"]
    for z, visited_min in by_zone.items():
        available = sum(p["visit_min"] for p in all_places if zone(p) == z)
        need = min(216, available)  # 40% of a 9h day
        assert visited_min >= need, f"{z}: only {visited_min} min scheduled"


def test_tight_budget_relaxes_gracefully():
    """A zero budget still plans (the worth-a-day rule relaxes, not errors)."""
    result = plan(budget=0, days=1)
    assert result["total_places"] >= 1
    assert result["total_cost"] == 0


def test_no_preferences_keeps_old_behaviour():
    """Without interest chips, weighting is unchanged (all categories 1.0)."""
    result = plan(budget=5000, days=2, cities=["Cairo", "Giza"])
    assert result["total_places"] >= 8  # dense classic Cairo trip still packs
