"""Ingest json data after running 'cloc' tool."""

import json
import os
from pathlib import Path
from typing import Any

from mq.tools.cloc.models import Cloc
from mq.tools.base import Scan


def ingest(scan: Scan, data: Any) -> int:
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

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
