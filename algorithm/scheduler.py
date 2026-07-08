"""Day-by-day scheduling of a selected set of places.

Takes the solver's selection and produces an ordered itinerary. Rules:
  - a ticket and the parent ticket it requires stay on the same day,
    parent first (the child is physically inside the parent site)
  - a day never mixes metro areas (Cairo/Giza vs Alexandria)
  - packing simulates the clock, so travel time, waiting for opening,
    and closing hours are respected while the day is being filled

Heuristic by design — the selection is provably optimal (see solver.py),
the schedule is a good-quality construction on top of it.
"""

import math

CITY_SPEED_KMH = 22       # average urban driving speed (Cairo traffic)
INTERCITY_SPEED_KMH = 80  # highway speed for hops > 50 km
MIN_TRAVEL_MIN = 8
DAY_START = 8 * 60        # 08:00


def _haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians,
                                 (float(a["lat"]), float(a["lon"]),
                                  float(b["lat"]), float(b["lon"])))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


def travel_minutes(a, b):
    km = _haversine_km(a, b)
    if km > 50:
        return round(km / INTERCITY_SPEED_KMH * 60) + 30  # buffer for leaving town
    return max(MIN_TRAVEL_MIN, round(km / CITY_SPEED_KMH * 60))


def _to_min(hhmm):
    h, m = hhmm.split(":")[:2]  # tolerate a stray HH:MM:SS in the data
    return int(h) * 60 + int(m)


def _fmt(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# Region map shared with the solver (see regions.py): a single day never
# spans regions that are hundreds of km apart.
from regions import REGION as _REGION, zone as _zone  # noqa: F401 (re-export)


def _clusters(places):
    """Group each place with the selected children that require it.

    Returns a list of units (lists of places), parent first. A unit is
    scheduled as a whole so a tomb never lands on a different day than
    the site it sits in.
    """
    ids = {p["id"] for p in places}
    units = {p["id"]: [p] for p in places
             if p["requires"].strip() not in ids}
    for p in places:
        parent = p["requires"].strip()
        if parent in ids:
            units[parent].append(p)
    return list(units.values())


def _simulate(order, day_start=DAY_START):
    """Walk an ordered day, returning stops with times and hour violations."""
    stops, violations = [], 0
    t = day_start
    prev = None
    for p in order:
        if prev is not None:
            t += travel_minutes(prev, p)
        opens, closes = _to_min(p["open"]), _to_min(p["close"])
        if t < opens:
            t = opens  # wait for opening
        late = t + p["visit_min"] > closes
        violations += late
        stops.append({"place": p, "arrive": t, "depart": t + p["visit_min"],
                      "after_hours": late})
        t += p["visit_min"]
        prev = p
    return stops, violations


def schedule(places, days, hours_per_day):
    """Assign places to `days` days of `hours_per_day` and order each day.

    Returns (day_plans, unscheduled). Each day plan:
    {"day": n, "city": str, "stops": [...], "total_cost": int, "end": "HH:MM"}
    """
    day_end_limit = DAY_START + round(hours_per_day * 60)
    remaining = list(places)
    day_plans = []

    for day_no in range(1, days + 1):
        units = _clusters(remaining)
        if not units:
            break
        # Seed the smallest remaining region first, so an isolated cluster
        # (e.g. Abu Simbel, far from everything) claims its own day instead of
        # being stranded once a bigger region fills the schedule. Within that,
        # prefer the earliest-closing unit, then the higher-rated one.
        zone_size = {}
        for u in units:
            zone_size[_zone(u[0])] = zone_size.get(_zone(u[0]), 0) + len(u)
        seed = min(units, key=lambda u: (zone_size[_zone(u[0])],
                                         min(_to_min(p["close"]) for p in u),
                                         -max(p["rating"] for p in u)))
        chain = list(seed)
        zone = _zone(chain[0])
        for p in seed:
            remaining.remove(p)
        _, violations = _simulate(chain)

        while True:
            best = None
            for unit in _clusters(remaining):
                if _zone(unit[0]) != zone:
                    continue
                stops, viol = _simulate(chain + unit)
                if viol > violations or stops[-1]["depart"] > day_end_limit:
                    continue
                dist = travel_minutes(chain[-1], unit[0])
                if best is None or dist < best[0]:
                    best = (dist, unit, viol)
            if best is None:
                break
            _, unit, violations = best
            chain.extend(unit)
            for p in unit:
                remaining.remove(p)

        stops, _ = _simulate(chain)
        cities = {p["city"] for p in chain}
        day_plans.append({
            "day": day_no,
            "city": " + ".join(sorted(cities)),
            "stops": stops,
            "total_cost": sum(p["price"] for p in chain),
            "end": _fmt(stops[-1]["depart"]) if stops else "",
        })

    return day_plans, remaining


def format_time(minutes):
    return _fmt(minutes)
