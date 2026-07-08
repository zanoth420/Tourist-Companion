"""Geographic regions: cities that share a day-trip zone.

Used by both the solver (to keep a selection to few coherent regions) and
the scheduler (to never mix regions within one day). Cities absent from the
map are their own zone (each coastal town stands alone).
"""

REGION = {
    "Cairo": "greater-cairo", "Giza": "greater-cairo",
    "Alexandria": "alexandria",
    "Luxor": "luxor",
    "Aswan": "aswan", "Edfu": "aswan", "Kom Ombo": "aswan",
    "Abu Simbel": "abu-simbel",
}


def zone(place) -> str:
    return REGION.get(place["city"], place["city"])
