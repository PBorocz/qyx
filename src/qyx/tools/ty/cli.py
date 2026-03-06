"""CLI Reporting for the TY type checker."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.ty.models import query_ty_0, query_ty_1, query_ty_2, query_ty_3, query_ty_h
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "ty", "ty")):
        log.error("Sorry, we haven't performed a 'ty' scan yet for this project.")
        return None

    log.debug(f"{scan=}")
    match args.level.lower():
        case Rl.SUMMARY:
            ty_0(args, project, scan)
        case Rl.DIRECTORY:
            ty_1(args, project, scan)
        case Rl.FILE:
            ty_2(args, project, scan)
        case Rl.GRANULAR:
            ty_3(args, project, scan)
        case Rl.HISTORY:
            ty_h(args, project)
        case Rl.ALL:
            ty_0(args, project, scan)
            ty_1(args, project, scan)
            ty_2(args, project, scan)
            ty_3(args, project, scan)
            ty_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")


def ty_0(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = query_ty_0(args, project, scan)

    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")

    table.add_row("Ty Checks", f"{result.count:,d}", "-")

    if result.violations_per_kloc:
        table.add_row(
            "Ty Checks Encountered per kLOC",
            f"{result.violations_per_kloc.score:.0f}",
            f"{result.violations_per_kloc.grade}",
        )
    if result.weighted_violations_per_kloc:
        table.add_row(
            "Weighted Ty Checks per kLOC",
            f"{result.weighted_violations_per_kloc.score:.0f}",
            f"{result.weighted_violations_per_kloc.grade}",
        )
    cli_console.print(table)


def ty_1(args: Namespace, project: Project, scan: Scan) -> None:
    results = query_ty_1(scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("Check", footer="TOTAL")
    table.add_column("Count", justify="right")
    for row in results.rows:
        table.add_row(row.check_name, f"{row.count:,d}")
    cli_console.print(table)


def ty_2(args: Namespace, project: Project, scan: Scan) -> None:
    results: Sns = query_ty_2(scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("Directory")
    table.add_column("Check")
    table.add_column("Count")
    for row in results.rows:
        table.add_row(row.directory, row.check_name, f"{row.count:,d}")
    cli_console.print(table)


def ty_3(args: Namespace, project: Project, scan: Scan) -> None:
    results: Sns = query_ty_3(scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("File")
    table.add_column("Check")
    table.add_column("Description")
    for row in results.rows:
        table.add_row(f"{row.directory}/{row.filename}", row.check_name, row.description)
    cli_console.print(table)


# History at the Rl.SUMMARY level...
def ty_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    result = query_ty_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="TY Results Over Time")
    table.add_column("-")
    for timestamp in sorted(result.timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
        )
    table.add_column("Delta")

    row = ["Checks"]
    for timestamp in sorted(result.timestamps):
        row.append(str(result.transposed[timestamp]))

    colors = args.config.get("renderers.cli.colors")
    color = colors["neutral"]
    if result.roc:
        if result.roc > 0.01:
            color = colors["positive"]
        elif result.roc < -0.01:
            color = colors["negative"]
        row.append(f"[{color}][bold]{result.roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)
