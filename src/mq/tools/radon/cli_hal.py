"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon import COLORS
from mq.tools.radon.models import query_hal, RadonHal
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def hal_0(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_hal(args, "0", scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for attr in RadonHal.attrs():
        table.add_row(attr.display, f"{getattr(row, attr.name):.2f}")
    cli_console.print(table)


def hal_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, mean_means = query_hal(args, "1", scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{mean_means[attr.name]:.2f}")
    for row in rows:
        t_row = [row.directory]
        for attr in RadonHal.attrs():
            t_row.append(f"{getattr(row, attr.name):.2f}")
        table.add_row(*t_row)
    cli_console.print(table)


def hal_2(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, means = query_hal(args, "2", scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{means[attr.name]:.2f}")
    for row in rows:
        t_row = [f"{row.directory}/{row.filename}"]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":
                value = f"{getattr(row, attr.name):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def hal_3(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, means = query_hal(args, "3", scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    table.add_column("Name", justify="left")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{means[attr.name]:.2f}")
    for row in rows:
        t_row = [f"{row.directory}/{row.filename}", row.name]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":
                value = f"{getattr(row, attr.name):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)


def hal_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_hal(args, "d", project=project, scan=scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    # fmt: off
    table.add_column("Metric" , justify="left")
    table.add_column("Value"  , justify="right")
    table.add_column("Grade"  , justify="center")
    table.add_row("Mean Bugs per kLOC"  , f"{row.bugs_d.score:.2f}"      , row.bugs_d.grade)
    table.add_row("Mean Difficulty"     , f"{row.difficulty_d.score:.2f}", row.difficulty_d.grade)
    table.add_row("Mean Effort per LOC" , f"{row.effort_d.score:.2f}"    , row.effort_d.grade)
    table.add_row("Composite Score"     , f"{row.composite_d.score:.2f}" , row.composite_d.grade)
    # fmt: on
    cli_console.print(table)


def hal_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, rocs = query_hal(args, "h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-HAL Results Over Time")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for attr, dt_rows in transposed.items():
        t_row = [attr]
        for timestamp in sorted(timestamps):
            t_row.append(f"{dt_rows[timestamp]:.2f}")

        if attr in rocs:
            roc = rocs[attr]
            t_value = ""
            if roc > 0.01:
                color = COLORS["positive"]
                t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"

            elif roc < -0.01:
                color = COLORS["negative"]
                t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)
        table.add_row(*t_row)

    cli_console.print(table)
