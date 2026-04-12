"""..."""

from collections import defaultdict
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.fxtd.models import Fxtd


def parse_save(scan: Scan, latest: bool, data: Any) -> int:
    def _get_summary(rows: list[Fxtd]) -> dict:
        """Calculate and return summary information."""
        return_ = defaultdict(int)
        for row in rows:
            return_[row.type] += 1
        return dict(return_)

    def _delimited_to_row(cwd: Path, s_result: str) -> Fxtd:
        if "|" not in s_result:
            return None
        (type_, dir_file, line, message) = s_result.split("|", 3)
        fn_path = Path(dir_file).relative_to(cwd) if dir_file.startswith("/") else Path(dir_file)
        return Fxtd(
            directory=fn_path.parent,
            filename=fn_path.name,
            type=type_,
            line=int(line),
            message=message.strip(),
        )

    # Parse
    rows = []
    for check in data.strip().split("\n"):
        if row := _delimited_to_row(scan.cwd, check):
            rows.append(row)

    # Save summary information (always)
    scan.summary = _get_summary(rows)
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            row.scan = scan.id
            row.save()
    return len(rows)
