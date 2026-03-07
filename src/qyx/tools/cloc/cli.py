"""CLI rendering obo 'cloc' tool."""

import logging
from argparse import Namespace
from types import SimpleNamespace as Sns

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools import format_int_or_percentage as fmt
from qyx.tools.base import Project, Scan, ToolType
from qyx.tools.cloc.models import query_cloc_0, query_cloc_1, query_cloc_2, query_cloc_d, query_cloc_h
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
            _render_0(args, scan)
        case Rl.DIRECTORY:
            _render_1(args, scan)
        case Rl.FILE:
            _render_2(args, scan)
        case Rl.DERIVED:
            _render_d(args, scan)
        case Rl.HISTORY:
            _render_h(args, project, scan)
        case Rl.ALL:
            _render_0(args, scan)
            _render_1(args, scan)
            _render_2(args, scan)
            _render_d(args, scan)
            _render_h(args, project, scan)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")


def _render_0(args: Namespace, scan: Scan) -> None:
    result = query_cloc_0(args, scan)
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


def _render_1(args: Namespace, scan: Scan, percentage: bool = False) -> None:
    grand_total: Sns = query_cloc_0(args, scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")

    footer = f"{grand_total.lines_code:,d} ({grand_total.lines_code_p:.1f}%)"
    table.add_column("LOC", justify="right", footer=footer)

    footer = f"{grand_total.lines_comment:,d} ({grand_total.lines_comment_p:.1f}%)"
    table.add_column("Comments", justify="right", footer=footer)

    footer = f"{grand_total.lines_blank:,d} ({grand_total.lines_blank_p:.1f}%)"
    table.add_column("Blank", justify="right", footer=footer)

    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, False))

    for result in query_cloc_1(args, scan).rows:
        table.add_row(
            result.directory,
            f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
            f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
            f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
            f"{result.lines_total:,d} ({result.lines_total_p:.1f}%)",
        )
    cli_console.print(table)


def _render_2(args: Namespace, scan: Scan) -> None:
    results: Sns = query_cloc_2(args, scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("LOC", justify="right", footer=fmt(results.column_totals["lines_code"], False))
    table.add_column("Comments", justify="right", footer=fmt(results.column_totals["lines_comment"], False))
    table.add_column("Blank", justify="right", footer=fmt(results.column_totals["lines_blank"], False))
    table.add_column("TOTAL", justify="right", footer=fmt(results.grand_total.lines_total, False))
    for row in results.rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            fmt(row.lines_code, False),
            fmt(row.lines_comment, False),
            fmt(row.lines_blank, False),
            fmt(row.lines_total, False),
        )
    cli_console.print(table)


def _render_d(args: Namespace, scan: Scan) -> None:
    result = query_cloc_d(args, scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Explanation", justify="left")
    table.add_row(
        "File Density",
        f"{result.avg_lines_per_file.score:.2f}",
        result.avg_lines_per_file.grade,
        "Average LOC per File",
    )
    table.add_row(
        "Code Density",
        f"{result.code_density.score:.2f}",
        result.code_density.grade,
        "LOC / (LOC + Blanks)",
    )
    table.add_row(
        "Comment Ratio",
        f"{result.comment_ratio.score:.2f}",
        result.comment_ratio.grade,
        "Comments / (Comment + LOC)",
    )
    cli_console.print(table)


def _render_h(args: Namespace, project: Project, scan: Scan) -> None:
    result = query_cloc_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)
    if len(result.timestamps) <= 20:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("Metric", justify="left", footer="-")
        for timestamp in sorted(result.timestamps):
            table.add_column(
                timestamps_formatted[timestamp],
                justify="right",
                footer=str(result.grand_totals[timestamp]),
                footer_style="bold cyan",
            )
        if result.roc["grand_total"]:
            table.add_column("Delta", justify="left", footer=f"{result.roc['grand_total']:,.2f}%")

        for metric, dt_rows in result.transposed.items():
            row = [metric]
            for timestamp in sorted(result.timestamps):
                row.append(str(dt_rows[timestamp]))
            if result.roc[metric]:
                row.append(f"{result.roc[metric]:+.2f}%")
            table.add_row(*row)
    else:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("", justify="left", footer="Mean Daily Growth")
        table.add_column("LOC", justify="right", footer=f"{result.adgs['total_code']:,.0f}")
        table.add_column("Comments", justify="right", footer=f"{result.adgs['total_comment']:,.0f}")
        table.add_column("Blank", justify="right", footer=f"{result.adgs['total_blank']:,.0f}")
        for row in result.rows:
            t_row = [
                timestamps_formatted[row.timestamp],
                f"{row.total_code:,d}",
                f"{row.total_comment:,d}",
                f"{row.total_blank:,d}",
            ]
            table.add_row(*t_row)

    cli_console.print(table)
