"""..."""

import json
import os
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.ruff.models import Ruff


def parse(scan: Scan, latest: bool, data: Any) -> int:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        # fmt: off
        ruff = Ruff(
            directory = fn_path.parent,
            filename  = fn_path.name,
            line      = ruff_result["location"]["row"],
            column    = ruff_result["location"]["column"],
            rule_code = ruff_result["code"],
            message   = ruff_result["message"],
            url       = ruff_result.get("url", ""),
        )
        # fmt: off
        return ruff

    # Parse
    rows = [_json_to_row(check) for check in json.loads(data)]

    # Save summary information (always)
    scan.summary = {"number_of_violations": len(rows)}
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            row.scan = scan.id
            row.save()

    return len(rows)
