"""CLI rendering obo 'cloc' tool."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.constants import ViewContext as Vc
from qyx.tools import format_int_or_percentage as fmt
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.cloc.models import query_0, query_1, query_2, query_d, query_h
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    # Get most recent Scan for simple "current-state" reporting..
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "cloc", "cloc")):
        log.error("Sorry, we haven't performed a CLOC measurement yet for this project.")
        return None

    match args.level.lower():
        case Rl.SUMMARY:
            cloc_0(args, scan)
        case Rl.DIRECTORY:
            cloc_1(args, scan)
        case Rl.FILE:
            cloc_2(args, scan)
        case Rl.DERIVED:
            cloc_d(args, scan)
        case Rl.HISTORY:
            cloc_h(args, project, scan)
        case Rl.ALL:
            cloc_0(args, scan)
            cloc_1(args, scan)
            cloc_2(args, scan)
            cloc_d(args, scan)
            cloc_h(args, project, scan)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")


def cloc_0(args: Namespace, scan: Scan) -> None:
    result = query_0(scan)
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


def cloc_1(args: Namespace, scan: Scan, percentage: bool = False) -> None:
    grand_total = query_0(scan)
    rows_directory_level = query_1(scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")

    footer = f"{grand_total.lines_code:,d} ({grand_total.lines_code_p:.1f}%)"
    table.add_column("LOC", justify="right", footer=footer)

    footer = f"{grand_total.lines_comment:,d} ({grand_total.lines_comment_p:.1f}%)"
    table.add_column("Comments", justify="right", footer=footer)

    footer = f"{grand_total.lines_blank:,d} ({grand_total.lines_blank_p:.1f}%)"
    table.add_column("Blank", justify="right", footer=footer)

    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, False))

    for result in rows_directory_level:
        table.add_row(
            result.directory,
            f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
            f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
            f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
            f"{result.lines_total:,d} ({result.lines_total_p:.1f}%)",
        )
    cli_console.print(table)


def cloc_2(args: Namespace, scan: Scan) -> None:
    rows, column_totals, grand_total = query_2(scan)

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


def cloc_d(args: Namespace, scan: Scan) -> None:
    row = query_d(args, scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Explanation", justify="left")
    table.add_row(
        "File Density",
        f"{row.avg_lines_per_file.score:.2f}",
        row.avg_lines_per_file.grade,
        "Average LOC per File",
    )
    table.add_row(
        "Code Density",
        f"{row.code_density.score:.2f}",
        row.code_density.grade,
        "LOC / (LOC + Blanks)",
    )
    table.add_row(
        "Comment Ratio",
        f"{row.comment_ratio.score:.2f}",
        row.comment_ratio.grade,
        "Comments / (Comment + LOC)",
    )
    cli_console.print(table)


def cloc_h(args: Namespace, project: Project, scan: Scan) -> None:
    timestamps, messages, rows, transposed, grand_totals, roc, adgs = query_h(project, last=5)
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
