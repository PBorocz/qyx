"""CLI rendering obo 'scc' tool."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import Project, Scan, ToolType
from qyx.tools.scc.models import query_scc_0

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, analysis: str) -> None:
    # Get most recent Scan for simple "current-state" reporting..
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_most_recent(project, "scc", "scc")):
        log.error("Sorry, we haven't performed a SCC measurement yet for this project.")
        return None

    match args.level.lower():
        case Rl.SUMMARY:
            _render_0(args, scan)
        # case Rl.DIRECTORY:
        #     _render_1(args, scan)
        # case Rl.FILE:
        #     _render_2(args, scan)
        # case Rl.HISTORY:
        #     _render_h(args, project, scan)
        case Rl.ALL:
            _render_0(args, scan)
            # _render_1(args, scan)
            # _render_2(args, scan)
            # _render_h(args, project, scan)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")


def _render_0(args: Namespace, scan: Scan) -> None:
    result = query_scc_0(args, scan)

    # Setup our table..
    table_args = dict(title=f"SCC @ {scan.as_of_display()}")
    if result.dryness:
        table_args["show_footer"] = True
    table = cli_table(**table_args)

    # Render table header (and footer if available)
    table.add_column("Metric", justify="left", footer="DRYness")
    for lang in result.report_languages:
        column_args = dict(justify="right")
        if result.dryness:
            column_args["footer"] = f"{result.dryness.get(lang).score}%"
        table.add_column(lang, **column_args)
    table.add_column("Total", justify="right")

    # Render
    for row in result.rows:
        if row.attr == "dryness":
            continue  # We already handled as a footer above!
        columns = [row.attr.title()]  # e.g. Code, Blanks etc..
        for lang in result.report_languages:
            columns.append(f"{row.languages.get(lang):,d}")  # e.g. Code for Python
        columns.append(f"{getattr(result.grand_totals, row.attr):,d}")  # Total Code across all languages

        table.add_row(*columns)

    cli_console.print(table)


# def _render_1(args: Namespace, scan: Scan, percentage: bool = False) -> None:
#     grand_total: Sns = query_scc_0(args, scan)
#     table = cli_table(title=f"SCC @ {scan.as_of_display()}", show_footer=True)
#     table.add_column("Directory", justify="left", footer="TOTAL")

#     footer = f"{grand_total.lines_code:,d} ({grand_total.lines_code_p:.1f}%)"
#     table.add_column("LOC", justify="right", footer=footer)

#     footer = f"{grand_total.lines_comment:,d} ({grand_total.lines_comment_p:.1f}%)"
#     table.add_column("Comments", justify="right", footer=footer)

#     footer = f"{grand_total.lines_blank:,d} ({grand_total.lines_blank_p:.1f}%)"
#     table.add_column("Blank", justify="right", footer=footer)

#     table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, False))

#     for result in query_scc_1(args, scan).rows:
#         table.add_row(
#             result.directory,
#             f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
#             f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
#             f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
#             f"{result.lines_total:,d} ({result.lines_total_p:.1f}%)",
#         )
#     cli_console.print(table)


# def _render_2(args: Namespace, scan: Scan) -> None:
#     results: Sns = query_scc_2(args, scan)

#     table = cli_table(title=f"SCC @ {scan.as_of_display()}", show_footer=True)
#     table.add_column("File", footer="TOTAL")
#     table.add_column("LOC", justify="right", footer=fmt(results.column_totals["lines_code"], False))
#     table.add_column("Comments", justify="right", footer=fmt(results.column_totals["lines_comment"], False))
#     table.add_column("Blank", justify="right", footer=fmt(results.column_totals["lines_blank"], False))
#     table.add_column("TOTAL", justify="right", footer=fmt(results.grand_total.lines_total, False))
#     for row in results.rows:
#         table.add_row(
#             f"{row.directory}/{row.filename}",
#             fmt(row.lines_code, False),
#             fmt(row.lines_comment, False),
#             fmt(row.lines_blank, False),
#             fmt(row.lines_total, False),
#         )
#     cli_console.print(table)


# def _render_h(args: Namespace, project: Project, scan: Scan) -> None:
#     result = query_scc_h(project, last=5)
#     timestamps_formatted = format_timestamp_headers(result.timestamps)
#     if len(result.timestamps) <= 20:
#         table = cli_table(title="SCC Results Over Time", show_footer=True)
#         table.add_column("Metric", justify="left", footer="-")
#         for timestamp in sorted(result.timestamps):
#             table.add_column(
#                 timestamps_formatted[timestamp],
#                 justify="right",
#                 footer=str(result.grand_totals[timestamp]),
#                 footer_style="bold cyan",
#             )
#         if result.roc["grand_total"]:
#             table.add_column("Delta", justify="left", footer=f"{result.roc['grand_total']:,.2f}%")

#         for metric, dt_rows in result.transposed.items():
#             row = [metric]
#             for timestamp in sorted(result.timestamps):
#                 row.append(str(dt_rows[timestamp]))
#             if result.roc[metric]:
#                 row.append(f"{result.roc[metric]:+.2f}%")
#             table.add_row(*row)
#     else:
#         table = cli_table(title="SCC Results Over Time", show_footer=True)
#         table.add_column("", justify="left", footer="Mean Daily Growth")
#         table.add_column("LOC", justify="right", footer=f"{result.adgs['total_code']:,.0f}")
#         table.add_column("Comments", justify="right", footer=f"{result.adgs['total_comment']:,.0f}")
#         table.add_column("Blank", justify="right", footer=f"{result.adgs['total_blank']:,.0f}")
#         for row in result.rows:
#             t_row = [
#                 timestamps_formatted[row.timestamp],
#                 f"{row.total_code:,d}",
#                 f"{row.total_comment:,d}",
#                 f"{row.total_blank:,d}",
#             ]
#             table.add_row(*t_row)

#     cli_console.print(table)
