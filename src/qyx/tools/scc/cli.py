"""CLI rendering obo 'scc' tool."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ALL_ITEMS
from qyx.constants import ReportLevel as Rl
from qyx.tools._models_ import Project, Scan, ToolDimension, ToolType
from qyx.tools.scc.models import query_scc_0, query_scc_1, query_scc_2, query_scc_h
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def render(args: Namespace, project: Project, o_tool: ToolType, o_dimension: ToolDimension | str) -> bool:
    # Get most recent Scan for simple "current-state" reporting..
    # Note: We safely can disregard whether or not the Scan was based on
    # git or directly from a directory as we're searching based on "as of",
    # thus, the most recent scan could be from either source!
    if not (scan := Scan.get_latest(project, "scc")):  # Note
        log.error("Sorry, we haven't performed a SCC measurement yet for this project.")
        return False

    match args.level.lower():
        case Rl.SUMMARY:
            _render_0(args, scan, o_dimension)
        case Rl.DIRECTORY:
            _render_1(args, scan, o_dimension)
        case Rl.FILE:
            _render_2(args, scan, o_dimension)
        case Rl.HISTORY:
            _render_h(args, project, scan, o_dimension)
        case Rl.ALL:
            _render_0(args, scan, o_dimension)
            _render_1(args, scan, o_dimension)
            _render_2(args, scan, o_dimension)
            _render_h(args, project, scan, o_dimension)
        case _:
            log.warning(f"Sorry, invalid report level: '{args.level}', run qyx report --help for valid options.")
            return False
    return True


def _render_0(args: Namespace, scan: Scan, dimension: ToolDimension | str) -> None:
    arg_dim = dimension.name if isinstance(dimension, ToolDimension) else dimension
    arg_dsc = dimension.description if isinstance(dimension, ToolDimension) else dimension
    result = query_scc_0(args, scan, arg_dim)
    if not vars(result):
        log.warning(f"Sorry, nothing matching dimension: '{args.dimension}'.")
        return

    # Setup our table..
    table = cli_table(title=f"SCC - {arg_dsc} @ {scan.as_of_display()}")

    # Render table header (and footer if available)
    table.add_column("Metric", justify="left", footer="DRYness")
    for lang in result.types:
        table.add_column(lang, justify="right")
    if len(result.types) > 1:
        table.add_column("Total", justify="right")

    # Render
    for model_attr in result.attrs:
        columns = [
            f"[bold]{model_attr.display}[/bold]",
        ]
        lang_data = result.rows[model_attr.name]
        for lang in result.types:
            columns.append(f"{lang_data.get(lang):,d}")

        # Add total entry if we have >1 languages *and* it's for # metric that's meaningfully summed!
        if len(result.types) > 1 and model_attr.name not in ("complexity", "dryness"):
            total = f"{getattr(result.grand_totals, model_attr.name):,d}"
            columns.append(f"[bold]{total}[/bold]")  # Total Code across all languages

        table.add_row(*columns)

        # Add section delimiters
        if model_attr.name in ("blank", "num_files"):
            table.add_section()

    cli_console.print(table)


def _render_1(args: Namespace, scan: Scan, dimension: ToolDimension | str, percentage: bool = False) -> None:
    if dimension == ALL_ITEMS:  # Can't have a wildcard here.
        log.warning("Sorry, a dimension is required to report on this level!.")
        return

    table = cli_table(title=f"SCC - {dimension.description} @ {scan.as_of_display()}")
    table.add_column("Directory", justify="left", footer="TOTAL")
    for attr in ("Lines", "Code", "Unique Code", "Comments", "Blanks", "Complexity", "Dryness"):
        table.add_column(attr, justify="right")

    for row in query_scc_1(args, scan, dimension.name).rows:
        l_row = [row.directory]
        for attr in ("lines", "code", "uloc", "comment", "blank", "complexity", "dryness"):
            try:
                l_row.append(f"{getattr(row, attr):,d}")
            except ValueError:
                l_row.append(f"{getattr(row, attr):.0f}")
        table.add_row(*l_row)
    cli_console.print(table)


def _render_2(args: Namespace, scan: Scan, dimension: ToolDimension, percentage: bool = False) -> None:
    if dimension == ALL_ITEMS:  # Can't have a wildcard here.
        log.warning("Sorry, a dimension is required to report on this level!.")
        return
    table = cli_table(title=f"SCC - {dimension.description} @ {scan.as_of_display()}")  # , show_footer=True)
    table.add_column("File", justify="left")
    for attr in ("Lines", "Code", "Unique Code", "Comments", "Blanks", "Complexity", "Dryness"):
        table.add_column(attr, justify="right")

    for row in query_scc_2(args, scan, dimension.name).rows:
        l_row = [f"{row.directory}/{row.filename}"]
        for attr in ("lines", "code", "uloc", "comment", "blank", "complexity", "dryness"):
            try:
                l_row.append(f"{getattr(row, attr):,d}")
            except ValueError:
                l_row.append(f"{getattr(row, attr):.0f}")
            except TypeError:
                l_row.append("")  # None
        table.add_row(*l_row)
    cli_console.print(table)


def _render_h(args: Namespace, project: Project, scan: Scan, dimension: ToolDimension) -> None:
    if dimension == ALL_ITEMS:  # Can't have a wildcard here.
        log.warning("Sorry, a dimension is required to report on this level!.")
        return

    result = query_scc_h(project, dimension.description, last=5)
    timestamps_formatted = format_timestamp_headers(result.timestamps)

    table = cli_table(title=f"SCC Results Over Time - {dimension.description}")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(result.timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    # START HERE!!! Make metric the nicer version as above
    for desc, metric in (
        ("Lines", "lines"),
        ("Code", "code"),
        ("Unique Code", "uloc"),
        ("Comments", "comment"),
        ("Blanks", "blank"),
        ("Complexity", "complexity"),
    ):
        dt_rows = result.transposed.get(metric)
        row = [desc]
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
