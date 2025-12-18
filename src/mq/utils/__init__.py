"""Common utilities."""

import os
import zoneinfo
from collections import defaultdict
from datetime import datetime

from loguru import logger


def remove_common_prefixes(rows: list) -> list:
    """Remove common prefix from a list of file paths."""
    if not rows:
        return []

    paths = [row.filename for row in rows]
    if not paths:
        return []

    # Find the common prefix
    common_prefix = os.path.commonpath(paths)

    for row in rows:
        row.filename = os.path.relpath(row.filename, common_prefix)
    return rows


def format_timestamp_headers(timestamps) -> dict[datetime, str]:
    """Format timestamp headers based on distribution across days/times..

    Args:
        timestamps: List of datetime objects

    Returns:
        Dict of formatted header strings keyed by original timestamp provided
    """

    def __local(dt: datetime) -> datetime:
        return dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone()

    if not timestamps:
        return []

    # Group timestamps by date
    dates_to_times = defaultdict(list)
    for ts in timestamps:
        date_key = ts.date()
        time_str = ts.strftime("%H:%M:%S")
        dates_to_times[date_key].append((ts, time_str))

    num_unique_dates = len(dates_to_times)
    logger.debug(f"{num_unique_dates=}")

    # Check if we have multiple times within any single date
    has_multiple_times_in_date = any(len(times) > 1 for times in dates_to_times.values())
    logger.debug(f"{has_multiple_times_in_date=}")

    # Determine format based on which case we have
    fmt_date = "%Y-%m-%d"
    fmt_time = "%H:%M"
    fmt_date_time = fmt_date + " " + fmt_time
    if num_unique_dates > 1 and has_multiple_times_in_date:
        fmt_ = fmt_date_time  # Case 1: Multiple dates AND multiple times within dates
        logger.debug("- case 1")
    elif num_unique_dates > 1:
        fmt_ = fmt_date  # Case 2: Multiple dates but only 1 timestamp per date
        logger.debug("- case 2")
    elif has_multiple_times_in_date:
        fmt_ = fmt_time  # Case 3: Single date but multiple times
        logger.debug("- case 3")
    else:
        fmt_ = fmt_date_time  # Single date, single time
        logger.debug("- case 4")

    return {ts: __local(ts).strftime(fmt_) for ts in timestamps}
