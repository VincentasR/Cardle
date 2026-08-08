from cardle.extract.data.table.version_table import VersionRow


def extract_version_power(
    rows: list[VersionRow],
) -> list[dict[str, str]]:
    """
    Extract Version -> raw power mappings.

    Power remains as raw Wikipedia text for now.
    Canonicalization will later convert it into a standard value,
    such as horsepower.
    """

    relationships: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        if row.version is None:
            continue

        if row.power is None:
            continue

        pair = (
            row.version,
            row.power,
        )

        if pair in seen:
            continue

        seen.add(pair)

        relationships.append(
            {
                "version": row.version,
                "power": row.power,
            }
        )

    return relationships