"""..."""

import json
import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.fxtd import COLORS
from mq.tools.fxtd.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def report(args: Namespace, o_tool, analysis: str) -> None:
    if not (project := Project.find_from_args(args)):
        log.error(f"Sorry, we didn't find any data yet for project: {args.project}")
        return None

    # Get most recent Scan for simple "current-state" reporting.
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "fxtd", "fxtd")):
        log.error("Sorry, we haven't performed a 'fxtd' scan yet for this project.")
        return None

    log.debug(f"{scan=}")
    match args.level.lower():
        case "0":
            _report_0(args, scan)
        case "1":
            _report_1(args, scan)
        case "2":
            _report_2(args, scan)
        case "h":
            _report_h(args, project)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run 'mq report --help' for valid options.")


def _report_0(args: Namespace, scan: Scan) -> None:
    results = query(args, "0", scan=scan)
    grand_total = sum([result.count for result in results])
    show_footer = True if results else False
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, f"{result.count:,d}")
    cli_console.print(table)


def _report_1(args: Namespace, scan: Scan) -> None:
    results = query(args, "1", scan=scan)
    grand_total = sum([result.count for result in results])
    show_footer = True if results else False

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Directory", footer="")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, result.directory, f"{result.count:,d}")
    cli_console.print(table)


def _report_2(args: Namespace, scan: Scan) -> None:
    rows = query(args, "2", scan=scan)
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")
    table.add_column("Type")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.type, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)


# History at the "0" level...
def _report_h(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, transposed, rocs = query(args, "history", project=project)
    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:,d}")

        roc = rocs.get(entity_type, 0)
        if roc > 0.01:
            color = COLORS["positive"]
        elif roc < -0.01:
            color = COLORS["negative"]
        else:
            color = COLORS["neutral"]

        t_row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*t_row)

    cli_console.print(table)


# History at the "1" level!
def _report_history(args: Namespace, project: Project) -> None:
    """Report on the history of scans "across"."""
    rows, messages, transposed, grand_totals = query(args, "history", project=project)
    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time", show_footer=True)
    table.add_column("Rule", justify="left", footer="TOTAL")
    table.add_column("Message", justify="left", footer="")
    timestamps = list({row.timestamp for row in rows})
    timestamps_formatted = format_timestamp_headers(timestamps)
    for timestamp in sorted(timestamps):
        table.add_column(
            timestamps_formatted[timestamp],
            justify="right",
            footer=str(grand_totals[timestamp]),
            footer_style="bold cyan",
        )

    for rule_code, dt_rows in transposed.items():
        row = [rule_code, messages[rule_code]]
        for timestamp in sorted(timestamps):
            row.append(str(dt_rows[timestamp]))
        table.add_row(*row)

    cli_console.print(table)
