"""..."""

import json
import os
from pathlib import Path
from typing import Any

from mq.tools.base import Scan
from mq.tools.ruff.models import Ruff


def parse(scan: Scan, data: Any) -> int:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        return Ruff(
            directory=fn_path.parent,
            filename=fn_path.name,
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            message=ruff_result["message"],
            rule_code=ruff_result["code"],
            url=ruff_result["url"],
        )

    # Parse
    rows = [_json_to_row(check) for check in json.loads(data)]

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
