"""..."""

import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from qyx.tools.scc.models import Scc, SccFile
from qyx.tools._models_ import Scan

log = logging.getLogger(__name__)


def parse_save(scan: Scan, latest: bool, data: Any) -> int:
    # Have to do this nested to reflect json file structure:
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse Scc scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    summary = defaultdict(lambda: dict)
    for language in json_:
        o_scc, d_scc = _generate_scc(scan, language)
        summary[o_scc.language] = d_scc
        if latest:
            o_scc.save()
            for file_info in language.get("Files", []):
                scc_file = _generate_scc_file(scan, o_scc, file_info)
                scc_file.save()

    # Always save the summary (which in this case, is essentially all the Scc rows into single dictionary!)
    scan.summary = summary
    scan.save()

    return len(json_)


def _generate_scc(scan: Scan, language: Any) -> (Scc, dict):
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

    # Derived attributes...
    scc.num_files = len(language.get("Files", []))
    if scc.code:
        scc.dryness = (scc.uloc / scc.code) * 100.0

    # fmt: off
    summary = dict(
        bytes               = scc.bytes,
        code_bytes          = scc.code_bytes,
        lines               = scc.lines,
        code                = scc.code,
        comment             = scc.comment,
        blank               = scc.blank,
        complexity          = scc.complexity,
        count               = scc.count,
        weighted_complexity = scc.weighted_complexity,
        uloc                = scc.uloc,
        num_files           = scc.num_files,
        dryness             = scc.dryness,
    )
    # fmt: on

    return scc, summary


def _generate_scc_file(scan: Scan, scc: Scc, file_info: dict) -> SccFile:
    fn_path = Path(file_info["Location"])
    fn_path = Path(os.path.relpath(fn_path, scan.cwd))
    assert file_info["Filename"] == fn_path.name
    scc_file = SccFile(
        scc=scc,
        location=file_info["Location"],
        filename=file_info["Filename"],
        directory=fn_path.parent,
        language=file_info["Language"].lower(),
        bytes=file_info["Bytes"],
        lines=file_info["Lines"],
        code=file_info["Code"],
        comment=file_info["Comment"],
        blank=file_info["Blank"],
        complexity=file_info["Complexity"],
        weighted_complexity=file_info["WeightedComplexity"],
        binary=file_info.get("Binary", False),
        minified=file_info.get("Minified", False),
        generated=file_info.get("Generated", False),
        endpoint=file_info.get("EndPoint", 0),
        uloc=file_info["Uloc"],
    )
    # fmt: on
    if scc_file.code:
        scc_file.dryness = (scc_file.uloc / scc_file.code) * 100.0
    return scc_file
