"""CLI rendering obo 'scc' tool."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import Project, Scan, ToolType
from qyx.tools.scc.models import query_scc_0, query_scc_1, query_scc_2, query_scc_h
from qyx.utils import format_timestamp_headers

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
        case Rl.DIRECTORY:
            _render_1(args, scan)
        case Rl.FILE:
            _render_2(args, scan)
        case Rl.HISTORY:
            _render_h(args, project, scan)
        case Rl.ALL:
            _render_0(args, scan)
            _render_1(args, scan)
            _render_2(args, scan)
            _render_h(args, project, scan)
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


def _render_1(args: Namespace, scan: Scan, percentage: bool = False) -> None:
    table = cli_table(title=f"SCC @ {scan.as_of_display()}")  # , show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")
    for attr in ("Lines", "Blank", "Comment", "Code", "ULOC", "Complexity"):
        table.add_column(attr, justify="right")

    for row in query_scc_1(args, scan).rows:
        l_row = [row.directory]
        for attr in ("lines", "blank", "comment", "code", "uloc", "complexity"):
            l_row.append(f"{getattr(row, attr):,d}")
        table.add_row(*l_row)
    cli_console.print(table)


def _render_2(args: Namespace, scan: Scan, percentage: bool = False) -> None:
    table = cli_table(title=f"SCC @ {scan.as_of_display()}")  # , show_footer=True)
    table.add_column("File", justify="left")
    for attr in ("Lines", "Blank", "Comment", "Code", "ULOC", "Complexity"):
        table.add_column(attr, justify="right")

    for row in query_scc_2(args, scan).rows:
        l_row = [f"{row.directory}/{row.filename}"]
        for attr in ("lines", "blank", "comment", "code", "uloc", "complexity"):
            l_row.append(f"{getattr(row, attr):,d}")
        table.add_row(*l_row)
    cli_console.print(table)


def _render_h(args: Namespace, project: Project, scan: Scan) -> None:
    result = query_scc_h(project, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)

    # FIXME: Could prolly use grand totals...
    table = cli_table(title="SCC Results Over Time")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(result.timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    for metric, dt_rows in result.transposed.items():
        row = [metric]

        for timestamp in sorted(result.timestamps):
            if metric == "dryness":
                value = f"{dt_rows[timestamp]:.2f}"
            else:
                value = f"{dt_rows[timestamp]:,d}"
            row.append(value)

        if result.roc[metric]:
            row.append(f"{result.roc[metric]:+.2f}%")
        table.add_row(*row)

    cli_console.print(table)
