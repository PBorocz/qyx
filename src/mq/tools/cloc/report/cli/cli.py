"""CLI report rendering dispatcher obo 'cloc' tool."""

import logging
from argparse import Namespace

from mq.tools.base import Project, Scan
from mq.tools.cloc.report.cli.cloc_0 import cloc_0
from mq.tools.cloc.report.cli.cloc_1 import cloc_1
from mq.tools.cloc.report.cli.cloc_2 import cloc_2
from mq.tools.cloc.report.cli.cloc_h import cloc_h

log = logging.getLogger(__name__)


def report(args: Namespace, o_tool, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Scan for simple "current-state" reporting..
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "cloc", "cloc")):
        log.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    match args.level.lower():
        case "0":
            cloc_0(scan)
        case "1":
            cloc_1(scan)
        case "2":
            cloc_2(scan)
        case "h":
            cloc_h(project, scan)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")
