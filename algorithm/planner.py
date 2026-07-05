"""End-to-end trip planner: optimal selection + day-by-day schedule.

Pipeline:
  1. solver.solve() picks the optimal affordable set of places
     (time-capped at ~85% of total trip hours to leave room for travel).
  2. scheduler.schedule() packs them into days and orders each day.
  3. If some places don't fit the days, the selection is re-solved with a
     tighter time cap (up to 3 attempts) so the final plan is consistent.

Usage:
  python planner.py --budget 5000 --days 3
  python planner.py --budget 2000 --days 2 --tier egyptian --student \
                    --prefer ancient=2 --prefer museum=1.5 --city Cairo --city Giza
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from solver import load_places, solve, DATA_FILE
from scheduler import schedule, format_time

TRAVEL_OVERHEAD = 0.85  # fraction of trip hours assumed available for visits


def plan(budget, tier="foreign", student=False, days=3, hours_per_day=9.0,
         weights=None, cities=None, data_file=DATA_FILE,
         locked=None, excluded=None, start_date=None):
    places = load_places(data_file, tier, student, cities)
    if not places:
        raise ValueError("No places match the given filters.")

    cap = round(days * hours_per_day * 60 * TRAVEL_OVERHEAD)
    for _ in range(3):
        chosen, status = solve(places, budget, max_minutes=cap, weights=weights,
                               locked=locked, excluded=excluded)
        if chosen is None:
            raise ValueError(f"No feasible plan (solver status: {status}). "
                             "If you locked places, they may not fit the budget.")
        day_plans, unscheduled = schedule(chosen, days, hours_per_day)
        if not unscheduled:
            break
        # didn't fit once travel time was accounted for — tighten and retry
        cap -= sum(p["visit_min"] for p in unscheduled)

    if start_date is not None:
        first = date.fromisoformat(start_date)
        for day in day_plans:
            day["date"] = (first + timedelta(days=day["day"] - 1)).isoformat()
    return {
        "params": {"budget": budget, "tier": tier, "student": student,
                   "days": days, "hours_per_day": hours_per_day},
        "days": day_plans,
        "unscheduled": unscheduled,
        "total_cost": sum(d["total_cost"] for d in day_plans),
        "total_places": sum(len(d["stops"]) for d in day_plans),
    }


def plan_as_json(**kwargs):
    """Same as plan() but with places flattened for API serialization."""
    result = plan(**kwargs)
    for day in result["days"]:
        day["stops"] = [{
            "id": s["place"]["id"],
            "name": s["place"]["name"],
            "city": s["place"]["city"],
            "area": s["place"]["area"],
            "category": s["place"]["category"],
            "price": s["place"]["price"],
            "rating": s["place"]["rating"],
            "arrive": format_time(s["arrive"]),
            "depart": format_time(s["depart"]),
            "after_hours": s["after_hours"],
            "needs_verification": s["place"]["needs_verification"] == "yes",
        } for s in day["stops"]]
    result["unscheduled"] = [p["name"] for p in result["unscheduled"]]
    return result


def parse_prefer(values):
    weights = {}
    for v in values or []:
        try:
            cat, w = v.split("=")
            weights[cat.strip()] = float(w)
        except ValueError:
            sys.exit(f"Bad --prefer value '{v}' (expected e.g. ancient=2)")
    return weights


def main():
    ap = argparse.ArgumentParser(description="Plan a full Egypt trip.")
    ap.add_argument("--budget", type=int, required=True, help="ticket budget in EGP")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--hours-per-day", type=float, default=9.0)
    ap.add_argument("--tier", choices=["foreign", "egyptian"], default="foreign")
    ap.add_argument("--student", action="store_true")
    ap.add_argument("--prefer", action="append", metavar="CATEGORY=WEIGHT",
                    help="e.g. --prefer ancient=2 (categories: ancient, islamic, "
                         "coptic, jewish, museum, palace, experience)")
    ap.add_argument("--city", action="append", help="limit to city (repeatable)")
    ap.add_argument("--data", type=Path, default=DATA_FILE)
    args = ap.parse_args()

    result = plan(args.budget, args.tier, args.student, args.days,
                  args.hours_per_day, parse_prefer(args.prefer), args.city,
                  args.data)

    print(f"\nTrip plan — {args.days} day(s), budget {args.budget} EGP "
          f"({args.tier} {'student' if args.student else 'adult'}):")
    for day in result["days"]:
        print(f"\n  Day {day['day']} — {day['city']} "
              f"({day['total_cost']} EGP, done by {day['end']})")
        for s in day["stops"]:
            p = s["place"]
            note = " (!after closing)" if s["after_hours"] else ""
            note += " *" if p["needs_verification"] == "yes" else ""
            print(f"    {format_time(s['arrive'])}-{format_time(s['depart'])}  "
                  f"{p['name']:<50} {p['price']:>6} EGP{note}")
    if result["unscheduled"]:
        print("\n  Could not fit:", ", ".join(p["name"] for p in result["unscheduled"]))
    print(f"\n  Total: {result['total_places']} places, "
          f"{result['total_cost']} EGP of {args.budget}\n")


if __name__ == "__main__":
    main()
