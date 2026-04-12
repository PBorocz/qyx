"""CLI Reporting for the TY type checker."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import Project, Scan, ToolDimension, ToolType
from qyx.tools.ga.models import query_ga_0

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, o_dimension: ToolDimension) -> bool:
    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_latest(project, "ga", "ga")):
        log.error("Sorry, we haven't performed a 'ga' scan yet for this project.")
        return False

    log.debug(f"{scan=}")
    match args.level.lower():
        case Rl.SUMMARY:
            ga_0(args, project, scan, o_dimension)
        # case Rl.DIRECTORY:
        #     ga_1(args, project, scan)
        # case Rl.FILE:
        #     ga_2(args, project, scan)
        # case Rl.GRANULAR:
        #     ga_3(args, project, scan)
        # case Rl.HISTORY:
        #     ga_h(args, project)
        case Rl.ALL:
            ga_0(args, project, scan, o_dimension)
        #     ga_1(args, project, scan)
        #     ga_2(args, project, scan)
        #     ga_3(args, project, scan)
        #     ga_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")
            return False
    return True


def ga_0(args: Namespace, project: Project, scan: Scan, o_dimension: ToolDimension) -> None:
    def _render_table(scan: Scan, title: str, column_l: str, column_r, rows: list[tuple[str, int]]) -> None:
        table = cli_table(title=f"{title} @ {scan.as_of_display()}")
        table.add_column(column_l, justify="left")
        table.add_column(column_r, justify="right")
        for row in rows:
            table.add_row(row[0], f"{row[1]:,d}")
        cli_console.print(table)

    result: Sns = query_ga_0(args, scan, o_dimension.name)
    if not result:
        cli_console.print("Sorry, no results found.")
        return

    match o_dimension.name:
        case "authorship":
            _render_table(scan, "GA-Top Committers/Authors", "Author", "# Commits", result.authorship)
        case "bug_commits":
            _render_table(scan, "GA-Files with Most Bug Commits", "File", "# Commits", result.bug_commits)
        case "commit_frequency":
            _render_table(scan, "GA-Commit Frequency", "Date/Month", "Commits", result.commit_frequency)
        case "emergency_commits":
            _render_table(scan, "GA-Files with Most Emergency Commits", "File", "# Commits", result.emergency_commits)
        case "file_churn":
            _render_table(scan, "GA-File Churn", "File", "# Commits", result.file_churn)
