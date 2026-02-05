"""CLI rendering obo 'fxtd' tool."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.constants import ReportLevel
from mq.utils.scoring import get_nested_config
from mq.tools.base import Project, Scan
from mq.tools.fxtd.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, o_tool, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "fxtd", "fxtd")):
        log.error("Sorry, we haven't performed an 'fxtd' scan yet for this project.")
        return None

    match args.level.lower():
        case ReportLevel.SUMMARY:
            fxtd_0(args, scan)
        case ReportLevel.DIRECTORY:
            fxtd_1(args, scan)
        case ReportLevel.FILE:
            fxtd_2(args, scan)
        case ReportLevel.DERIVED:
            fxtd_d(args, project, scan)
        case ReportLevel.HISTORY:
            fxtd_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'mq report --help' for valid options.")


def fxtd_0(args: Namespace, scan: Scan) -> None:
    results = query(args, ReportLevel.SUMMARY, scan=scan)
    grand_total = sum([result.count for result in results])
    show_footer = True if results else False
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, f"{result.count:,d}")
    cli_console.print(table)


def fxtd_1(args: Namespace, scan: Scan) -> None:
    results = query(args, ReportLevel.DIRECTORY, scan=scan)
    grand_total = sum([result.count for result in results])
    show_footer = True if results else False

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Directory", footer="")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, result.directory, f"{result.count:,d}")
    cli_console.print(table)


def fxtd_2(args: Namespace, scan: Scan) -> None:
    rows = query(args, ReportLevel.FILE, scan=scan)
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")
    table.add_column("Type")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.type, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


def fxtd_d(args: Namespace, project: Project, scan: Scan) -> None:
    rows, composite = query(args, ReportLevel.DERIVED, project=project, scan=scan)

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")

    if not rows:
        table.add_row("Congratulations..No issues found!")
        cli_console.print(table)
        return

    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")

    for row in rows:
        table.add_row(
            f"{row.type}'s per kLOC",
            f"{row.fxtd_d.score:.2f}",
            f"{row.fxtd_d.grade}",
        )
    table.add_row(
        "Composite (weighted)",
        f"{composite.score:.2f}",
        composite.grade,
    )
    cli_console.print(table)


def fxtd_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, transposed, rocs = query(args, ReportLevel.HISTORY, project=project, last=5)

    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = get_nested_config(args.config, "renderers.cli.colors")
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
