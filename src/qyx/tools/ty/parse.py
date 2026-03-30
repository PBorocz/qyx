"""..."""

import json
import os
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.ty.models import Ty, TyDescription


def parse(scan: Scan, data: Any) -> int:
    def _json_to_row(ty_result: dict, is_git: bool) -> Ty:
        fn_path = Path(ty_result["location"]["path"])
        if not is_git:
            fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        description, _ = TyDescription.get_or_create(value=ty_result["description"])
        return Ty(
            directory=fn_path.parent,
            filename=fn_path.name,
            line=ty_result["location"]["positions"]["begin"]["line"],
            column=ty_result["location"]["positions"]["begin"]["column"],
            description=description,
            severity=ty_result["severity"],
            check_name=ty_result["check_name"],
            fingerprint=ty_result["fingerprint"],
        )

    # Parse
    rows = [_json_to_row(check, scan.request.is_git) for check in json.loads(data)]

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
