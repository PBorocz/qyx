"""..."""

from pathlib import Path

from mq.tools.base import Scan
from mq.tools.ruff.models import Ruff


def ingest(scan: Scan, data: list) -> int:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        return Ruff(
            dir=fn_path.parent,
            filename=fn_path.name,
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            message=ruff_result["message"],
            rule_code=ruff_result["code"],
            url=ruff_result["url"],
        )

    # Parse
    rows = [_json_to_row(check) for check in data]

    # Save
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)
