"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.constants import ReportLevel
from mq.tools.base import Project, Scan
from mq.tools.radon import COLORS
from mq.tools.radon.models import query_cc
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def cc_0(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, ReportLevel.SUMMARY, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Entity Type")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def cc_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, ReportLevel.DIRECTORY, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("Directory", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            row.directory,
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def cc_2(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, ReportLevel.FILE, scan)
    table = cli_table(title=f"RADON-CC @ {scan.as_of_display()}")
    table.add_column("File", justify="left")
    table.add_column("Entity Type", justify="left")
    table.add_column("Complexity", justify="right")
    table.add_column("Rank", justify="center")
    plurals = dict(Function="Functions", Method="Methods", Class="Classes")
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            plurals[row.entity_type],
            f"{row.mean_complexity:.2f}",
            row.get_rank(row.mean_complexity),
        )
    cli_console.print(table)


def cc_3(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, ReportLevel.DETAIL, scan)
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


def cc_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, ReportLevel.DERIVED, project=project, scan=scan)
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


def cc_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, roc = query_cc(args, ReportLevel.HISTORY, project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:.2f}")

        t_value = ""
        roc_ = roc.get(entity_type, 0)
        if roc_ > 0.01:
            color = COLORS["negative"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        elif roc_ < -0.01:
            color = COLORS["positive"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)

        table.add_row(*t_row)

    cli_console.print(table)
