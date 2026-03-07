"""..."""

import json
from pathlib import Path
from typing import Any

from qyx.tools.base import Scan
from qyx.tools.ty.models import Ty


def parse(scan: Scan, data: Any) -> int:
    def _json_to_row(ty_result: dict) -> Ty:
        fn_path = Path(ty_result["location"]["path"])
        return Ty(
            directory=fn_path.parent,
            filename=fn_path.name,
            line=ty_result["location"]["positions"]["begin"]["line"],
            column=ty_result["location"]["positions"]["begin"]["column"],
            description=ty_result["description"],
            severity=ty_result["severity"],
            check_name=ty_result["check_name"],
            fingerprint=ty_result["fingerprint"],
        )

    # Parse
    rows = [_json_to_row(check) for check in json.loads(data)]

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
