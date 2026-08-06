from cardle.extract.data.table.version_table import VersionRow


def extract_versions(
    rows: list[VersionRow],
) -> list[str]:
    """
    Extract unique version names from parsed version rows.
    """

    versions: list[str] = []
    seen: set[str] = set()

    for row in rows:
        if row.version is None:
            continue

        if row.version in seen:
            continue

        seen.add(row.version)
        versions.append(row.version)

    return versions