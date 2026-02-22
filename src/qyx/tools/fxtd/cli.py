"""CLI rendering obo 'fxtd' tool."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.fxtd.models import query
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
            fxtd_1(args, project, scan)
        case Rl.FILE:
            fxtd_2(args, project, scan)
        case Rl.HISTORY:
            fxtd_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'qyx report --help' for valid options.")


def fxtd_0(args: Namespace, project: Project, scan: Scan) -> None:
    rows, grand_total, composite = query(args, Rl.SUMMARY, project, scan)

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=True)

    if not rows:
        table.add_row("Congratulations..No issues found!")
        cli_console.print(table)
        return

    table.add_column("Type", justify="left", footer="Composite (weighted)")
    table.add_column("Count", justify="right", footer=f"{grand_total:,d}")
    table.add_column("Per kLOC", justify="right", footer=f"{composite.score:.2f}")
    table.add_column("Grade", justify="center", footer=composite.grade)

    for row in rows:
        table.add_row(
            f"{row.type}",
            f"{row.count}",
            f"{row.metric.score:.2f}",
            f"{row.metric.grade}",
        )
    cli_console.print(table)


def fxtd_1(args: Namespace, project: Project, scan: Scan) -> None:
    results, grand_total = query(args, Rl.DIRECTORY, project, scan)
    show_footer = True if results else False

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Directory", footer="")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, result.directory, f"{result.count:,d}")
    cli_console.print(table)


def fxtd_2(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query(args, Rl.FILE, project, scan)
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")
    table.add_column("Type")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.type, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


def fxtd_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, _, transposed, rocs = query(args, Rl.HISTORY, project, None, last=5)

    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            if timestamp in values:
                t_row.append(f"{values[timestamp]:,d}")
            else:
                t_row.append("")

        roc = rocs.get(entity_type, 0)
        if roc > 0.01:
            color = colors["positive"]
        elif roc < -0.01:
            color = colors["negative"]
        else:
            color = colors["neutral"]

        t_row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*t_row)

    cli_console.print(table)
