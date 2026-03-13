"""..."""

import json
import os
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.ruff.models import Ruff, RuffMessage, RuffUrl


def parse(scan: Scan, data: Any) -> int:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))

        message, _ = RuffMessage.get_or_create(value=ruff_result["message"])

        if ruff_result.get("url"):  # Optional field(?)
            url, _ = RuffUrl.get_or_create(value=ruff_result["url"])
        else:
            url = None

        ruff = Ruff(
            directory=fn_path.parent,
            filename=fn_path.name,
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            rule_code=ruff_result["code"],
            message=message,
        )
        if url:
            ruff.url = url

        return ruff

    # Parse
    rows = [_json_to_row(check) for check in json.loads(data)]

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
