import json

from cardle.canonical.pipeline import build_canonical_dataset


with open(
    "data/raw/toyota_raw.json",
    encoding="utf-8",
) as f:
    raw_data = json.load(f)


canonical = build_canonical_dataset(raw_data)


with open(
    "data/canonical/auris_canonical.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        canonical,
        f,
        indent=2,
        ensure_ascii=False,
    )