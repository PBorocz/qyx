"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.constants import ReportLevel
from mq.utils.scoring import get_nested_config
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def mi_0(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_mi(args, ReportLevel.SUMMARY, scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row(
        "Composite Maintainability Score",
        f"{row.mi_mean:.2f}",
    )
    cli_console.print(table)


def mi_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, mean_mi_mean, mean_mi_mean_footer, show_footer = query_mi(args, ReportLevel.DIRECTORY, scan)

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index", justify="right", footer=mean_mi_mean_footer)
    for row in rows:
        table.add_row(
            row.directory,
            f"{row.mi_mean:.2f}",
        )
    cli_console.print(table)


def mi_2(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, avg_footer, show_footer = query_mi(args, ReportLevel.FILE, scan)

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Filename", justify="left", footer="(simple mean)")
    table.add_column("Maintainability Index", justify="right", footer=avg_footer)
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.directory,
            row.filename,
            f"{row.mi:.2f}",
            row.rank,
        )
    cli_console.print(table)


def mi_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_mi(args, ReportLevel.DERIVED, project=project, scan=scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}")
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    table.add_row(
        "Maintainability",
        f"{row.mi_d.score:.1f}",
        row.mi_d.grade,
    )
    cli_console.print(table)


def mi_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, roc = query_mi(args, ReportLevel.HISTORY, project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    colors = get_nested_config(args.config, "renderers.cli.colors")
    for metric, dt_rows in transposed.items():
        row = ["Maintainability Index"]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:.2f}")

        if roc > 0.01:
            color = colors["positive"]
        elif roc < -0.01:
            color = colors["negative"]
        else:
            color = colors["neutral"]

        row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*row)
    cli_console.print(table)
