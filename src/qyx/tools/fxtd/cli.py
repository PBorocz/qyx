"""CLI rendering obo 'fxtd' tool."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.fxtd.models import query_fxtd_0, query_fxtd_1, query_fxtd_2, query_fxtd_h
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "fxtd", "fxtd")):
        log.error("Sorry, we haven't performed an 'fxtd' scan yet for this project.")
        return None

    match args.level.lower():
        case Rl.SUMMARY:
            fxtd_0(args, project, scan)
        case Rl.DIRECTORY:
            fxtd_1(scan)
        case Rl.FILE:
            fxtd_2(scan)
        case Rl.HISTORY:
            fxtd_h(args, project)
        case Rl.ALL:
            fxtd_0(args, project, scan)
            fxtd_1(scan)
            fxtd_2(scan)
            fxtd_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")


def fxtd_0(args: Namespace, project: Project, scan: Scan) -> None:
    result: Sns = query_fxtd_0(args, scan)
    if not result.rows:
        cli_console.print("[yellow]Congratulations! No issues found.[/yellow]")
        return

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=True)

    table.add_column("Type", justify="left", footer="Composite (weighted)")
    table.add_column("Count", justify="right", footer=f"{result.grand_total:,d}")
    table.add_column("Per kLOC", justify="right", footer=f"{result.metric_composite_weighted.score:.2f}")
    table.add_column("Grade", justify="center", footer=result.metric_composite_weighted.grade)

    for row in result.rows:
        table.add_row(
            f"{row.type}",
            f"{row.count}",
            f"{row.metric.score:.2f}",
            f"{row.metric.grade}",
        )
    cli_console.print(table)


def fxtd_1(scan: Scan) -> None:
    results = query_fxtd_1(scan)
    show_footer = True if results else False

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Directory", footer="")
    table.add_column("Count", justify="center", footer=f"{results.grand_total:,}")
    for result in results.rows:
        table.add_row(result.type, result.directory, f"{result.count:,d}")
    cli_console.print(table)


def fxtd_2(scan: Scan) -> None:
    results = query_fxtd_2(scan)
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")
    table.add_column("Type")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in results.rows:
        table.add_row(row.type, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


def fxtd_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    result = query_fxtd_h(project, last=5)

    timestamps_formatted = format_timestamp_headers(result.timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time")
    table.add_column("-")
    for timestamp in sorted(result.timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for entity_type, values in result.transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(result.timestamps):
            if timestamp in values:
                t_row.append(f"{values[timestamp]:,d}")
            else:
                t_row.append("")

        roc = result.rocs.get(entity_type, 0)
        if roc > 0.01:
            color = colors["positive"]
        elif roc < -0.01:
            color = colors["negative"]
        else:
            color = colors["neutral"]

        t_row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*t_row)

    cli_console.print(table)
