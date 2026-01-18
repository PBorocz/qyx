"""CLI report rendering obo 'cloc' tool."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.tools import format_int_or_percentage as fmt
from mq.tools.base import Project, Scan
from mq.tools.cloc.models import query
from mq.utils import format_timestamp_headers

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
            _report_0(scan)
        case "1":
            _report_1(scan)
        case "2":
            _report_2(scan)
        case "h":
            _report_h(project, scan)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run mq report --help for valid options.")


def _report_0(scan: Scan) -> None:
    result = query("0", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}")
    table.add_column("LOC", justify="center")
    table.add_column("Comments", justify="center")
    table.add_column("Blanks", justify="center")
    table.add_column("TOTAL", justify="center")
    table.add_row(
        f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
        f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
        f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
        f"{result.lines_total:,d}",
    )
    cli_console.print(table)


def _report_1(scan: Scan, percentage: bool = False) -> None:
    grand_total = query("0", scan=scan)
    detail_rows = query("1", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")

    footer = f"{grand_total.lines_code:,d} ({grand_total.lines_code_p:.1f}%)"
    table.add_column("LOC", justify="right", footer=footer)

    footer = f"{grand_total.lines_comment:,d} ({grand_total.lines_comment_p:.1f}%)"
    table.add_column("Comments", justify="right", footer=footer)

    footer = f"{grand_total.lines_blank:,d} ({grand_total.lines_blank_p:.1f}%)"
    table.add_column("Blank", justify="right", footer=footer)

    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, False))

    for result in detail_rows:
        table.add_row(
            result.directory,
            f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
            f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
            f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
            f"{result.lines_total:,d} ({result.lines_total_p:.1f}%)",
        )
    cli_console.print(table)


def _report_2(scan: Scan) -> None:
    rows, column_totals, grand_total = query("2", scan=scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("LOC", justify="right", footer=fmt(column_totals["lines_code"], False))
    table.add_column("Comments", justify="right", footer=fmt(column_totals["lines_comment"], False))
    table.add_column("Blank", justify="right", footer=fmt(column_totals["lines_blank"], False))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total, False))
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            fmt(row.lines_code, False),
            fmt(row.lines_comment, False),
            fmt(row.lines_blank, False),
            fmt(row.lines_total, False),
        )
    cli_console.print(table)


def _report_h(project: Project, scan: Scan) -> None:
    timestamps, rows, transposed, grand_totals, roc, adgs = query("h", project=project, scan=scan, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    if len(timestamps) <= 20:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("Metric", justify="left", footer="-")
        for timestamp in sorted(timestamps):
            table.add_column(
                timestamps_formatted[timestamp],
                justify="right",
                footer=str(grand_totals[timestamp]),
                footer_style="bold cyan",
            )
        if roc["grand_total"]:
            table.add_column("Delta", justify="left", footer=f"{roc['grand_total']:,.2f}%")

        for metric, dt_rows in transposed.items():
            row = [metric]
            for timestamp in sorted(timestamps):
                row.append(str(dt_rows[timestamp]))
            if roc[metric]:
                row.append(f"{roc[metric]:+.2f}%")
            table.add_row(*row)
    else:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("", justify="left", footer="Mean Daily Growth")
        table.add_column("LOC", justify="right", footer=f"{adgs['total_code']:,.0f}")
        table.add_column("Comments", justify="right", footer=f"{adgs['total_comment']:,.0f}")
        table.add_column("Blank", justify="right", footer=f"{adgs['total_blank']:,.0f}")
        for row in rows:
            t_row = [
                timestamps_formatted[row.timestamp],
                f"{row.total_code:,d}",
                f"{row.total_comment:,d}",
                f"{row.total_blank:,d}",
            ]
            table.add_row(*t_row)

    cli_console.print(table)
