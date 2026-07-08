"""Regression: selections must be geographically and thematically coherent.

The original bugs: boosting "nature" with no city filter produced one short
stop per day scattered across half of Egypt, and the trip filled up with
off-theme mosques and churches (short free high-rated places win the
value-per-minute race).
"""

import pytest

from planner import plan
from regions import zone
from solver import DATA_FILE, load_places

THEMES = {"ancient", "islamic", "coptic", "jewish", "palace"}  # non-nature themes


def _scenario():
    return plan(budget=3000, days=3, weights={"nature": 2})


def _stops(result):
    return [s["place"] for d in result["days"] for s in d["stops"]]


def test_at_most_one_region_per_day():
    result = _scenario()
    zones = {zone(p) for p in _stops(result)}
    assert len(zones) <= 3


def test_other_themes_are_excluded():
    """A nature trip contains no mosques, churches, tombs or palaces —
    only nature plus neutral leisure (museums, promenades)."""
    cats = {p["category"] for p in _stops(_scenario())}
    assert not cats & THEMES, f"off-theme categories crept in: {cats & THEMES}"


def test_every_day_serves_the_interest():
    """Each day must contain the chosen theme — a region can't earn a day
    on neutral fillers alone (kills the Cairo-churches day)."""
    result = _scenario()
    for day in result["days"]:
        assert any(s["place"]["category"] == "nature" for s in day["stops"]), \
            f"day {day['day']} ({day['city']}) has no nature stop"


def test_visited_regions_are_worth_the_trip():
    """Each visited region contributes a real chunk of on-theme time
    (or everything on-theme it has)."""
    result = _scenario()
    all_places = load_places(DATA_FILE, "foreign", False, None)
    by_zone: dict[str, int] = {}
    for p in _stops(result):
        if p["category"] == "nature":
            by_zone[zone(p)] = by_zone.get(zone(p), 0) + p["visit_min"]
    for z, visited_min in by_zone.items():
        available = sum(p["visit_min"] for p in all_places
                        if zone(p) == z and p["category"] == "nature")
        need = min(216, available)  # 40% of a 9h day
        assert visited_min >= need, f"{z}: only {visited_min} on-theme min"


def test_locked_place_survives_theme_filter():
    """Locking a mosque onto a nature trip keeps it — pins are deliberate."""
    result = plan(budget=3000, days=2, cities=["Sharm el-Sheikh"],
                  weights={"nature": 2}, locked=["mustafa-mosque"])
    assert "mustafa-mosque" in {p["id"] for p in _stops(result)}


def test_interests_with_no_matches_error_clearly():
    """Nature in Cairo/Giza (no nature places) must explain, not scatter."""
    with pytest.raises(ValueError, match="interests"):
        plan(budget=3000, days=2, cities=["Cairo", "Giza"],
             weights={"nature": 2})


def test_tight_budget_relaxes_gracefully():
    """A zero budget still plans (the worth-a-day rule relaxes, not errors)."""
    result = plan(budget=0, days=1)
    assert result["total_places"] >= 1
    assert result["total_cost"] == 0


def test_no_preferences_keeps_old_behaviour():
    """Without interest chips, weighting is unchanged (all categories 1.0)."""
    result = plan(budget=5000, days=2, cities=["Cairo", "Giza"])
    assert result["total_places"] >= 8  # dense classic Cairo trip still packs
