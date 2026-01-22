"""..."""

import logging
from argparse import Namespace

from mq.tools.base import Project, Scan
from mq.tools.ruff.report.cli.ruff_0 import ruff_0
from mq.tools.ruff.report.cli.ruff_1 import ruff_1
from mq.tools.ruff.report.cli.ruff_2 import ruff_2
from mq.tools.ruff.report.cli.ruff_h import ruff_h

log = logging.getLogger(__name__)


def report(args: Namespace, o_tool, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "ruff", "ruff")):
        log.error("Sorry, we haven't performed a 'ruff' scan yet for this project.")
        return None

    log.debug(f"{scan=}")
    match args.level.lower():
        case "0":
            ruff_0(scan)
        case "1":
            ruff_1(scan)
        case "2":
            ruff_2(scan)
        case "h":
            ruff_h(project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'mq report --help' for valid options.")
