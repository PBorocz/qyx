"""Common utilities."""

import os


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
