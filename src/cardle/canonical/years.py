import re


def parse_year_range(value: str) -> tuple[int | None, int | None]:
    """
    Extract the first and last 4-digit year from a string.

    Example:
        "January 1976 – April 1989 86,216 produced"
        -> (1976, 1989)
    """
    years = re.findall(r"\b(?:18|19|20)\d{2}\b", value)

    if not years:
        return None, None

    start_year = int(years[0])

    if len(years) == 1:
        return start_year, None

    end_year = int(years[-1])

    return start_year, end_year