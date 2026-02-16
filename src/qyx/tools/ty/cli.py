"""CLI Reporting for the TY type checker."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.ty.models import query
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
        case ReportLevel.SUMMARY:
            ty_0(args, scan)
        case ReportLevel.DIRECTORY:
            ty_1(args, scan)
        case ReportLevel.FILE:
            ty_2(args, scan)
        case ReportLevel.DETAIL:
            ty_3(args, scan)
        case ReportLevel.DERIVED:
            ty_d(args, project, scan)
        case ReportLevel.HISTORY:
            ty_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")


def ty_0(args: Namespace, scan: Scan) -> None:
    row = query(args, ReportLevel.SUMMARY, scan=scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row("Issues", f"{row.count:,d}")
    cli_console.print(table)


def ty_1(args: Namespace, scan: Scan) -> None:
    summary = query(args, ReportLevel.SUMMARY, scan=scan)
    results = query(args, ReportLevel.DIRECTORY, scan=scan)
    show_footer = True if results else False
    table = cli_table(title=f"TY @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Check", footer="TOTAL")
    table.add_column("Count", justify="right", footer=f"{summary.count:,}")
    # table.add_column("Description")
    for result in results:
        table.add_row(result.check_name, f"{result.count:,d}")
    cli_console.print(table)


def ty_2(args: Namespace, scan: Scan) -> None:
    rows = query(args, ReportLevel.FILE, scan=scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("Directory")
    table.add_column("Check")
    table.add_column("Count")
    for row in rows:
        table.add_row(row.directory, row.check_name, f"{row.count:,d}")
    cli_console.print(table)


def ty_3(args: Namespace, scan: Scan) -> None:
    rows = query(args, ReportLevel.DETAIL, scan=scan)
    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("File")
    table.add_column("Check")
    table.add_column("Description")
    for row in rows:
        table.add_row(f"{row.directory}/{row.filename}", row.check_name, row.description)
    cli_console.print(table)


def ty_d(args: Namespace, project: Project, scan: Scan) -> None:
    row = query(args, ReportLevel.DERIVED, project=project, scan=scan)

    table = cli_table(title=f"TY @ {scan.as_of_display()}")
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    if row.violations_per_kloc:
        table.add_row(
            "Ty Checks Encountered per kLOC",
            f"{row.violations_per_kloc.score:.0f}",
            f"{row.violations_per_kloc.grade}",
        )
    if row.weighted_violations_per_kloc:
        table.add_row(
            "Weighted Ty Checks per kLOC",
            f"{row.weighted_violations_per_kloc.score:.0f}",
            f"{row.weighted_violations_per_kloc.grade}",
        )
    cli_console.print(table)


# History at the ReportLevel.SUMMARY level...
def ty_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, _, rows, roc = query(args, ReportLevel.HISTORY, project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="TY Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
        )
    table.add_column("Delta")

    row = ["Checks"]
    for timestamp in sorted(timestamps):
        row.append(str(rows[timestamp]))

    colors = args.config.get("renderers.cli.colors")
    color = colors["neutral"]
    if roc:
        if roc > 0.01:
            color = colors["positive"]
        elif roc < -0.01:
            color = colors["negative"]
        row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)


#
# Still used??
#
# def _report_history(project: Project) -> None:
#     """Report on the history of scans "across" at the ReportLevel.DIRECTORY level."""
#     rows, messages, transposed, grand_totals = query(args, ReportLevel.HISTORY, project=project, last=5)
#     ################################################################################################
#     # Render the table
#     ################################################################################################
#     table = cli_table(title="TY Results Over Time", show_footer=True)
#     table.add_column("Rule", justify="left", footer="TOTAL")
#     table.add_column("Message", justify="left", footer="")
#     timestamps = list({row.timestamp for row in rows})
#     timestamps_formatted = format_timestamp_headers(timestamps)
#     for timestamp in sorted(timestamps):
#         table.add_column(
#             timestamps_formatted[timestamp],
#             justify="right",
#             footer=str(grand_totals[timestamp]),
#             footer_style="bold cyan",
#         )

#     for check_name, dt_rows in transposed.items():
#         row = [check_name, messages[check_name]]
#         for timestamp in sorted(timestamps):
#             row.append(str(dt_rows[timestamp]))
#         table.add_row(*row)

#     cli_console.print(table)
