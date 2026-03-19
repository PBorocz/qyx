"""..."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from qyx.tools.scc.models import Scc, SccFile
from qyx.tools._models_ import Scan

log = logging.getLogger(__name__)


def parse(scan: Scan, data: Any) -> int:
    # Have to do this nested to reflect json file structure:
    count = 0
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse Scc scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    for language in json_:
        # fmt: off
        scc = Scc(
            scan                = scan.id,
            language            = language["Name"].lower(), # eg. python, html, etc.
            bytes               = language["Bytes"],
            code_bytes          = language["CodeBytes"],
            lines               = language["Lines"],
            code                = language["Code"],
            comment             = language["Comment"],
            blank               = language["Blank"],
            complexity          = language["Complexity"],
            count               = language["Count"],
            weighted_complexity = language["WeightedComplexity"],
            uloc                = language["ULOC"],
        )
        # fmt: off

        # Derived attributes...
        scc.num_files = len(language.get("Files", []))
        if scc.code:
            scc.dryness = (scc.uloc / scc.code) * 100.0
        scc.save()
        count += 1

        for file_info in language.get("Files", []):
            fn_path = Path(file_info["Location"])
            fn_path = Path(os.path.relpath(fn_path, scan.cwd))
            assert file_info["Filename"] == fn_path.name
            # fmt: off
            scc_file = SccFile(
                scc                 = scc,
                location            = file_info["Location"],
                filename            = file_info["Filename"],
                directory           = fn_path.parent,
                language            = file_info["Language"].lower(),
                bytes               = file_info["Bytes"],
                lines               = file_info["Lines"],
                code                = file_info["Code"],
                comment             = file_info["Comment"],
                blank               = file_info["Blank"],
                complexity          = file_info["Complexity"],
                weighted_complexity = file_info["WeightedComplexity"],
                binary              = file_info.get("Binary", False),
                minified            = file_info.get("Minified", False),
                generated           = file_info.get("Generated", False),
                endpoint            = file_info.get("EndPoint", 0),
                uloc                = file_info["Uloc"],
            )
            # fmt: on
            if scc_file.code:
                scc_file.dryness = (scc_file.uloc / scc_file.code) * 100.0
            scc_file.save()

    return count
