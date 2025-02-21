"""Validation utilities for the Nefino MCP server."""

from datetime import datetime


def validate_date_format(date_str: str | None) -> bool:
    """Validate that a date string is in YYYY-MM-DD format."""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_date_range(
    begin_date: str | None, end_date: str | None
) -> tuple[bool, str | None]:
    """Validate a date range.

    Args:
        begin_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not begin_date or not end_date:
        return True, None

    try:
        begin = datetime.strptime(begin_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if begin > end:
            return False, "Begin date must be before or equal to end date"

        return True, None
    except ValueError:
        return False, "Dates must be in YYYY-MM-DD format"


def validate_last_n_days(days: int | None) -> tuple[bool, str | None]:
    """Validate last_n_days parameter.

    Args:
        days: Number of days to look back

    Returns:
        Tuple of (is_valid, error_message)
    """
    if days is None:
        return True, None

    if not isinstance(days, int):
        return False, "last_n_days must be an integer"

    if days < 0:
        return False, "last_n_days must be zero or positive"

    return True, None
