"""Parse json data after running 'cloc' tool."""

import logging
from pathlib import Path

from mq.tools.cloc.models import Cloc


log = logging.getLogger(__name__)


def parse_json(data: dict) -> list[Cloc]:
    def _json_to_row(fn_: str, cloc_result: dict) -> Cloc:
        fn_path = Path(fn_)
        assert fn_path.name
        return Cloc(
            dir=fn_path.parent,
            filename=fn_path.name,
            lines_blank=cloc_result["blank"],
            lines_code=cloc_result["code"],
            lines_comment=cloc_result["comment"],
        )

    return [_json_to_row(fn_, check) for fn_, check in data.items() if fn_ not in ("header", "SUM")]
