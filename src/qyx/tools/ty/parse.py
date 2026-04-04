"""..."""

import json
import os
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.ty.models import Ty


def parse(scan: Scan, latest: bool, data: Any) -> int:
    def _json_to_row(ty_result: dict, is_git: bool) -> Ty:
        fn_path = Path(ty_result["location"]["path"])
        if not is_git:
            fn_path = Path(os.path.relpath(fn_path, scan.cwd))

        # fmt: off
        ty_ = Ty(
            directory   = fn_path.parent,
            filename    = fn_path.name,
            line        = ty_result["location"]["positions"]["begin"]["line"],
            column      = ty_result["location"]["positions"]["begin"]["column"],
            description = ty_result["description"],
            severity    = ty_result["severity"],
            check_name  = ty_result["check_name"],
            fingerprint = ty_result["fingerprint"],
        )
        # fmt: on
        return ty_

    # Parse
    rows = [_json_to_row(check, scan.request.is_git) for check in json.loads(data)]

    # Save summary information (always)
    scan.summary = {"number_of_violations": len(rows)}
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            row.scan = scan.id
            row.save()
    return len(rows)
