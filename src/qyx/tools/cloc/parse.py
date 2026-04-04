"""Ingest json data after running 'cloc' tool."""

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from qyx.tools.cloc.models import Cloc
from qyx.tools._models_ import Scan


def parse(scan: Scan, latest: bool, data: Any) -> int:
    def _json_to_row(fn_: str, cloc_result: dict) -> Cloc:
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
        return Cloc(
            directory=fn_path.parent,
            filename=fn_path.name,
            lines_blank=cloc_result["blank"],
            lines_code=cloc_result["code"],
            lines_comment=cloc_result["comment"],
        )

    # Parse..
    json_ = json.loads(data)
    rows = [_json_to_row(fn_, check) for fn_, check in json_.items() if fn_ not in ("header", "SUM")]

    # Save summary information (always)
    scan.summary = _get_summary(rows)
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            row.scan = scan.id
            row.save()
    return len(rows)


def _get_summary(rows: list[Cloc]) -> dict:
    """Calculate and return summary information."""
    return_ = defaultdict(int)
    for row in rows:
        return_["lines_blank"] += row.lines_blank
        return_["lines_code"] += row.lines_code
        return_["lines_comment"] += row.lines_comment
        return_["lines_total"] += row.lines_blank + row.lines_code + row.lines_comment
    return return_
