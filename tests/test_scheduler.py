"""The schedule must keep dependency clusters together and days coherent."""

from planner import plan
from scheduler import _to_min


def all_stops(result):
    return [(d, s) for d in result["days"] for s in d["stops"]]


def test_dependent_tickets_same_day_parent_first():
    result = plan(budget=8000, days=4)
    for day in result["days"]:
        ids = [s["place"]["id"] for s in day["stops"]]
        for s in day["stops"]:
            parent = s["place"]["requires"].strip()
            if parent:
                assert parent in ids, "child scheduled without parent on same day"
                assert ids.index(parent) < ids.index(s["place"]["id"]), \
                    "parent must come before child"


def test_no_region_mixing_within_a_day():
    """A single day must stay within one geographic region — never mix, say,
    Luxor with Cairo or Alexandria."""
    from scheduler import _zone
    result = plan(budget=20000, days=8)
    for day in result["days"]:
        zones = {_zone(s["place"]) for s in day["stops"]}
        assert len(zones) == 1, f"day {day['day']} mixed regions: {zones}"


def test_days_end_within_limit():
    hours = 9
    result = plan(budget=8000, days=3, hours_per_day=hours)
    day_end_limit = 8 * 60 + hours * 60
    for day in result["days"]:
        assert day["stops"][-1]["depart"] <= day_end_limit


def test_stops_respect_opening_hours():
    result = plan(budget=5000, days=3)
    for day, stop in all_stops(result):
        p = stop["place"]
        assert stop["arrive"] >= _to_min(p["open"])
        if not stop["after_hours"]:
            assert stop["depart"] <= _to_min(p["close"])


def test_total_cost_matches_days():
    result = plan(budget=5000, days=3)
    assert result["total_cost"] == sum(d["total_cost"] for d in result["days"])
    assert result["total_cost"] <= 5000
