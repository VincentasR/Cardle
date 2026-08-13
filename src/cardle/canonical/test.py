import json

from cardle.canonical.relationships import resolve_relationships
from cardle.canonical.vehicle import canonicalize_vehicle


with open("data/raw/e24_test.json", encoding="utf-8") as f:
    raw_data = json.load(f)


canonical_vehicles = [
    canonicalize_vehicle(raw_vehicle)
    for raw_vehicle in raw_data
]


canonical_vehicles = resolve_relationships(canonical_vehicles)


with open(
    "data/canonical/e24_canonical.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        canonical_vehicles,
        f,
        indent=2,
        ensure_ascii=False,
    )