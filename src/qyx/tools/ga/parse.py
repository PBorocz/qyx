"""..."""

import json
import logging
from pathlib import Path
from typing import Any

from qyx.tools._models_ import Scan
from qyx.tools.ga.models import Ga

log = logging.getLogger(__name__)


def parse_save(scan: Scan, latest: bool, data: Any) -> int:
    # The script returns a single line representing the temp file containing our JSON results.
    try:
        temp_file_path = Path(data.strip())
        with open(temp_file_path, "r") as fh_:
            data = json.load(fh_)
    except FileNotFoundError:
        log.critical(f"Sorry, temp file from 'ga_tool.py' not found: {temp_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {temp_file_path}")
        # Still try to delete the corrupted file
        if temp_file_path.exists():
            temp_file_path.unlink()
        return None

    ga_ = Ga(scan=scan.id)
    for chunk, datum in data.items():
        setattr(ga_, chunk, datum)
        ga_.save()

    return len(data)
