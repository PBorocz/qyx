"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi


log = logging.getLogger(__name__)


def mi_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_mi(args, "d", project=project, scan=scan)
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
