"""Common utilities."""

import logging
import zoneinfo
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger(__name__)


def dt_to_local(timestamp: str) -> str:
    """Convert a db-based timestamp to local."""
    # Parse the string timestamp from database
    dt_utc = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp

    # Ensure it's timezone-aware (it should be already)
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

    # Return as local timezone
    return dt_utc.astimezone()


def dt_to_display(timestamp: str, collapse_today=False) -> str:
    """..."""
    # Parse the string timestamp from database to local time.
    dt_local = dt_to_local(timestamp)

    # Choose format based on whether it's today and we want to collapse today's date.
    format = "%Y-%m-%d %H:%M%p"  # Default format..
    if collapse_today and dt_local.date() == datetime.now().date():
        format = "%I:%M%p"

    return dt_local.strftime(format)


def rate_of_change_percentage(old_value: int | float, new_value: int | float) -> float | None:
    """Calculate the rate of change percentage between two values.

    Args:
        old_value (float): The original/older value
        new_value (float): The newer value

    Returns:
        float: The rate of change as a percentage

    Raises:
        ZeroDivisionError: If old_value is zero
    """
    if old_value == 0:
        # log.warning("Cannot calculate rate of change when old_value is 0.0")
        return None

    assert isinstance(new_value, (int, float)), f"Sorry, got {new_value=} {type(new_value)=}"
    assert isinstance(old_value, (int, float)), f"Sorry, got {old_value=} {type(old_value)=}"

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


def parse_path_arg(arg_path: str) -> tuple[str, str, bool]:
    """Parse user input and return (normalised, display_string).

    Args:
        arg_path: Command-line argument from user

    Returns:
        tuple: (normalised, name)
    """
    # Check if it's a URL
    if arg_path.startswith(("http://", "https://", "git@")):
        normalised = arg_path

        # Parse URL to get project name
        if arg_path.startswith("git@"):
            # Handle git@github.com:user/project.git format
            project_part = arg_path.split(":")[-1]
            name = project_part.rstrip("/").split("/")[-1].removesuffix(".git")
        else:
            parsed = urlparse(arg_path)
            path_parts = parsed.path.rstrip("/").split("/")
            name = path_parts[-1].removesuffix(".git")

        return name, normalised, True

    # It's a file path (relative or absolute or ".")
    # Convert to absolute path
    path = Path(arg_path).resolve()
    normalised = str(path)

    # Get the last component of the path for display
    name = path.name

    return name, normalised, False


def bucket(datum: list, bucket_breaks: list[float], as_percentage: bool = True) -> list[tuple[str, int]]:
    """Calculate histogram of values provided expressed either raw or as a percentage of the total.

    Args:
        datum: List of data values to bucket.
        bucket_breaks: Bucket boundaries (default: [0, 50, 100, 200, ...])
        as_percentage: If true, return values as percentage of total, else raw count.

    Returns:
        List of (bucket_label, count) tuples in sorted order.
    """
    if bucket_breaks[-1] != float("inf"):
        bucket_breaks.append(float("inf"))

    raw_histogram = defaultdict(int)
    total = 0.0
    for value in datum:
        bucket_label = _get_bucket_label(value, bucket_breaks)
        raw_histogram[bucket_label] += 1
        total += value

    # Convert to percentage of total?
    if as_percentage:
        histogram = {label: (value / len(datum)) * 100.0 for label, value in raw_histogram.items()}
    else:
        histogram = raw_histogram

    # Return as list of tuples with all buckets (even if zero); in order!
    return_ = []
    for i in range(len(bucket_breaks) - 1):
        label = _format_bucket_label(i, bucket_breaks)
        count = histogram.get(label, 0)
        return_.append((label, count))
    return return_


def _get_bucket_label(value: float, breaks: list[float]) -> str:
    """Find which bucket a value falls into."""
    for i in range(len(breaks) - 1):
        if breaks[i] <= value < breaks[i + 1]:
            return _format_bucket_label(i, breaks)
    # Shouldn't reach here if breaks include inf
    return _format_bucket_label(len(breaks) - 2, breaks)


def _format_bucket_label(index: int, breaks: list[float]) -> str:
    """Format a bucket label like '0-50', '50-100', '1000+'."""
    lower = int(breaks[index])
    upper = breaks[index + 1]

    if upper == float("inf"):
        return f"{lower}+"
    else:
        return f"{lower}-{int(upper) - 1}"
