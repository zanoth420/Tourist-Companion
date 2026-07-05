"""Tourist Companion itinerary selector.

Selects the optimal set of attractions for a given budget (and optional
time limit) using Google OR-Tools CP-SAT. Unlike the earlier genetic
algorithm, this is exact: the returned selection is provably optimal.

Constraints handled:
  - budget: total ticket cost <= budget (per visitor tier)
  - time (optional): total visit minutes <= --hours
  - requires: interior/tomb tickets need the parent site's entry ticket
  - excludes: combo tickets can't be combined with their components

Usage:
  python solver.py --budget 3000
  python solver.py --budget 1500 --tier egyptian --student --hours 12
  python solver.py --budget 5000 --city Giza --city Cairo
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("OR-Tools is required: pip install ortools")

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "places.csv"


def price_column(tier, student):
    return f"price_{tier}_{'student' if student else 'adult'}"


def load_places(path, tier, student, cities):
    col = price_column(tier, student)
    places = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if cities and row["city"] not in cities:
                continue
            raw = row[col].strip()
            if raw == "":
                continue  # no ticket tier for this visitor type
            row["price"] = int(raw)
            row["visit_min"] = int(row["visit_min"])
            row["rating"] = float(row["rating"])
            places.append(row)
    return places


def place_value(place, weights=None):
    """Integer objective value: rating scaled by the category preference weight."""
    w = (weights or {}).get(place["category"], 1.0)
    return round(place["rating"] * 10 * w)


def solve(places, budget, max_minutes=None, weights=None, locked=None, excluded=None):
    """locked: place ids that must be in the plan; excluded: ids that must not.

    Excluded places are removed before solving, so anything that requires
    them drops out too (via the parent-missing rule below). A locked id that
    isn't available (filtered, excluded, or wrong tier) raises ValueError.
    """
    if excluded:
        places = [p for p in places if p["id"] not in set(excluded)]

    model = cp_model.CpModel()
    by_id = {p["id"]: p for p in places}
    x = {p["id"]: model.new_bool_var(p["id"]) for p in places}

    for pid in locked or []:
        if pid not in by_id:
            raise ValueError(f"Locked place '{pid}' is not available with the "
                             "current filters/exclusions.")
        model.add(x[pid] == 1)

    model.add(sum(x[p["id"]] * p["price"] for p in places) <= budget)
    if max_minutes is not None:
        model.add(sum(x[p["id"]] * p["visit_min"] for p in places) <= max_minutes)

    for p in places:
        parent = p["requires"].strip()
        if parent:
            if parent in by_id:
                model.add_implication(x[p["id"]], x[parent])
            else:
                # parent filtered out (e.g. by --city): child is unreachable
                model.add(x[p["id"]] == 0)
        for other in filter(None, p["excludes"].split(";")):
            other = other.strip()
            if other in by_id:
                model.add(x[p["id"]] + x[other] <= 1)

    model.maximize(sum(x[p["id"]] * place_value(p, weights) for p in places))

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, status
    chosen = [p for p in places if solver.value(x[p["id"]])]
    return chosen, status


def main():
    ap = argparse.ArgumentParser(description="Build an optimal Egypt itinerary.")
    ap.add_argument("--budget", type=int, required=True, help="ticket budget in EGP")
    ap.add_argument("--tier", choices=["foreign", "egyptian"], default="foreign")
    ap.add_argument("--student", action="store_true", help="use student prices")
    ap.add_argument("--hours", type=float, help="cap total sightseeing hours")
    ap.add_argument("--city", action="append", help="limit to city (repeatable)")
    ap.add_argument("--data", type=Path, default=DATA_FILE)
    args = ap.parse_args()

    places = load_places(args.data, args.tier, args.student, args.city)
    if not places:
        sys.exit("No places match the given filters.")

    max_minutes = round(args.hours * 60) if args.hours else None
    chosen, status = solve(places, args.budget, max_minutes)
    if chosen is None:
        sys.exit(f"No feasible itinerary (solver status: {status}).")

    chosen.sort(key=lambda p: (p["city"], p["area"], -p["rating"]))
    total_cost = sum(p["price"] for p in chosen)
    total_min = sum(p["visit_min"] for p in chosen)

    tier_label = f"{args.tier} {'student' if args.student else 'adult'}"
    print(f"\nOptimal itinerary ({tier_label}, budget {args.budget} EGP):\n")
    current_city = None
    for p in chosen:
        if p["city"] != current_city:
            current_city = p["city"]
            print(f"  {current_city}")
        flag = " *" if p["needs_verification"] == "yes" else ""
        print(f"    {p['name']:<50} {p['price']:>6} EGP   "
              f"{p['visit_min']:>3} min   rating {p['rating']}{flag}")
    print(f"\n  {len(chosen)} places | total {total_cost} EGP "
          f"of {args.budget} | ~{total_min / 60:.1f} hours of visits")
    if any(p["needs_verification"] == "yes" for p in chosen):
        print("  * price not officially confirmed — verify before relying on it")
    print(f"  Solution is {'provably optimal' if status == cp_model.OPTIMAL else 'feasible'}.\n")


if __name__ == "__main__":
    main()
