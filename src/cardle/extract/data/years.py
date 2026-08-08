from cardle.extract.data.table.version_table import VersionRow


def extract_version_years(
    rows: list[VersionRow],
) -> list[dict[str, str]]:
    """
    Extract Version -> raw production years mappings.

    Years remain as raw Wikipedia text for now.
    Canonicalization will later turn them into start_year / end_year.
    """

    relationships: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        if row.version is None:
            continue

        if row.years is None:
            continue

        pair = (
            row.version,
            row.years,
        )

        if pair in seen:
            continue

        seen.add(pair)

        relationships.append(
            {
                "version": row.version,
                "years": row.years,
            }
        )

    return relationships