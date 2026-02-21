"""..."""

import logging
from argparse import Namespace

from qyx.cli import cli_console, cli_table
from qyx.constants import ReportLevel
from qyx.tools.base import Project, Scan
from qyx.tools.radon.models import query_cc
from qyx.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def cc_0(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query_cc(args, ReportLevel.SUMMARY, project, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Entity Type")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.entity_type,
            f"{row.complexity:.2f}",
            row.rank,
        )
    cli_console.print(table)


def cc_1(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query_cc(args, ReportLevel.DIRECTORY, project, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            row.directory,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.rank,
        )
    cli_console.print(table)


def cc_2(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query_cc(args, ReportLevel.FILE, project, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_type,
            f"{row.complexity:.2f}",
            row.rank,
        )
    cli_console.print(table)


def cc_3(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query_cc(args, ReportLevel.DETAIL, project, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Name", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            row.entity_name,
            row.entity_type,
            f"{row.complexity:.2f}",
            row.rank,
        )
    cli_console.print(table)


def cc_d(args: Namespace, project: Project, scan: Scan) -> None:
    rows = query_cc(args, ReportLevel.DERIVED, project, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Entity Type", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            f"{row.entity_type}",
            f"{row.cc_d.score:.1f}",
            row.cc_d.grade,
        )
    cli_console.print(table)


def cc_h(args: Namespace, project: Project, scan: Scan) -> None:
    timestamps, _, transposed, roc = query_cc(args, ReportLevel.HISTORY, project, None, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    colors = args.config.get("renderers.cli.colors")
    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:.2f}")

        t_value = ""
        roc_ = roc.get(entity_type, 0)
        if roc_ > 0.01:
            color = colors["negative"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        elif roc_ < -0.01:
            color = colors["positive"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)

        table.add_row(*t_row)

    cli_console.print(table)
