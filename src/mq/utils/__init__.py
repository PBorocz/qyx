"""Common utilities."""

import logging
import os
import zoneinfo
from collections import defaultdict
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


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


def timestamp_display(timestamp: str, full: bool = False) -> str:
    """..."""
    # Parse the string timestamp from database
    if isinstance(timestamp, str):
        dt_utc = datetime.fromisoformat(timestamp)
    else:
        dt_utc = timestamp

    # Ensure it's timezone-aware (it should be already)
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

    # Convert to local timezone
    dt_local = dt_utc.astimezone()

    # Choose format based on whether it's today
    if not full and dt_local.date() == datetime.now().date():
        format = "%H:%M%p"
    else:
        format = "%Y-%m-%d %H:%M%p"

    return dt_local.strftime(format)


def rate_of_change_percentage(old_value, new_value):
    """Calculate the rate of change percentage between two values.

    Args:
        old_value (float): The original value
        new_value (float): The new value

    Returns:
        float: The rate of change as a percentage

    Raises:
        ZeroDivisionError: If old_value is zero
    """
    if old_value == 0:
        raise ZeroDivisionError("Cannot calculate rate of change when old_value is zero")

    return ((new_value - old_value) / old_value) * 100


def format_timestamp_headers(timestamps) -> dict[datetime, str]:
    """Format timestamp headers based on distribution across days/times..

    Args:
        timestamps: List of datetime objects

    Returns:
        Dict of formatted header strings keyed by original timestamp provided
    """

    def __local(s_dt: str) -> datetime:
        return datetime.fromisoformat(s_dt).astimezone()

    if not timestamps:
        return []

    # Group timestamps by date
    dates_to_times = defaultdict(list)
    for ts in timestamps:
        date_ = datetime.fromisoformat(ts)
        date_key = date_.date()
        time_str = date_.strftime("%H:%M:%S")
        dates_to_times[date_key].append((ts, time_str))

    num_unique_dates = len(dates_to_times)
    log.debug(f"{num_unique_dates=}")

    # Check if we have multiple times within any single date
    has_multiple_times_in_date = any(len(times) > 1 for times in dates_to_times.values())
    log.debug(f"{has_multiple_times_in_date=}")

    # Determine format based on which case we have
    fmt_date = "%Y-%m-%d"
    fmt_time = "%H:%M"
    fmt_date_time = fmt_date + " " + fmt_time
    if num_unique_dates > 1 and has_multiple_times_in_date:
        fmt_ = fmt_date_time  # case "1": Multiple dates AND multiple times within dates
        log.debug("- case 1")
    elif num_unique_dates > 1:
        fmt_ = fmt_date  # case "2": Multiple dates but only 1 timestamp per date
        log.debug("- case 2")
    elif has_multiple_times_in_date:
        fmt_ = fmt_time  # Case 3: Single date but multiple times
        log.debug("- case 3")
    else:
        fmt_ = fmt_date_time  # Single date, single time
        log.debug("- case 4")

    return {ts: __local(ts).strftime(fmt_) for ts in timestamps}


def detect_project_name(resolved_path: str) -> str | None:
    """Detect Python project name from common config files."""
    path = Path(resolved_path)

    # Walk up the directory tree looking for project indicators
    for parent in [path] + list(path.parents):
        # Git repository name
        if (parent / ".git").exists():
            return parent.name

        # pyproject.toml
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    if name := data.get("project", {}).get("name"):
                        return name
                    if name := data.get("tool", {}).get("poetry", {}).get("name"):
                        return name
            except Exception:
                pass

        # setup.py fallback
        if (parent / "setup.py").exists():
            return parent.name

    return None
