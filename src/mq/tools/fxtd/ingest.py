"""..."""

import os
from pathlib import Path
from typing import Any

from mq.tools.base import Scan
from mq.tools.fxtd.models import Fxtd


def ingest(scan: Scan, data: Any) -> int:
    def _delimited_to_row(s_result: str) -> Fxtd:
        if "|" not in s_result:
            return None
        (type_, dir_file, line, message) = s_result.split("|", 3)
        fn_path = Path(dir_file)
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        return Fxtd(
            directory=fn_path.parent,
            filename=fn_path.name,
            type=type_,
            line=int(line),
            message=message.strip(),
        )

    # Parse
    rows = []
    for check in data.decode("utf-8").strip().split("\n"):
        if row := _delimited_to_row(check):
            rows.append(row)

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
