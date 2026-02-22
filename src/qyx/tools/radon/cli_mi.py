"""..."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel as Rl
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import query_mi
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def mi_0(args: Namespace, project: Project, scan: Scan) -> None:
    mi_, metric = query_mi(args, Rl.SUMMARY, project, scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_header=False)
    table.add_column("Composite Maintainability Score (Weighted)", style="bold magenta")
    table.add_column(f"{mi_:.2f}", style="bold magenta")
    table.add_column(metric.grade, style="bold magenta")
    cli_console.print(table)


def mi_1(args: Namespace, project: Project, scan: Scan) -> None:
    mi_metric, mi_by_directory = query_mi(args, Rl.DIRECTORY, project, scan)
    show_footer = True if mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index (Weighted)", justify="right", footer=f"{mi_metric.score:.2f}")
    for directory, mi_dir in mi_by_directory.items():
        table.add_row(
            directory,
            f"{mi_dir:.2f}",
        )
    cli_console.print(table)


def mi_2(args: Namespace, project: Project, scan: Scan) -> None:
    mi_metric, rows = query_mi(args, Rl.FILE, project, scan)
    show_footer = True if mi_metric else False

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Filename", justify="left")
    table.add_column("Maintainability Index", justify="right", footer=f"{mi_metric.score:.2f}")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.directory,
            row.filename,
            f"{row.mi:.2f}",
            row.rank,
        )
    cli_console.print(table)


def mi_h(args: Namespace, project: Project, scan: Scan) -> None:
    _, rows, roc = query_mi(args, Rl.HISTORY, project, None, last=5)
    timestamps = list(rows.keys())
    timestamps_formatted = format_timestamp_headers(timestamps)

    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    row = ["Maintainability Index"]
    for timestamp in sorted(timestamps):
        row.append(f"{rows[timestamp]:.2f}")

    colors = args.config.get("renderers.cli.colors")
    if roc > 0.01:
        color = colors["negative"]
    elif roc < -0.01:
        color = colors["positive"]
    else:
        color = colors["neutral"]

    row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

    table.add_row(*row)

    cli_console.print(table)
