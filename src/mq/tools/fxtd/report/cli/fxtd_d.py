"""CLI report rendering obo 'fxtd' tool for level d or derived data."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.tools.base import Project, Scan
from mq.tools.fxtd.models import query

log = logging.getLogger(__name__)


def fxtd_d(args: Namespace, project: Project, scan: Scan) -> None:
    rows, composite = query(args, "d", project=project, scan=scan)

    table = cli_table(title=f"FXTD @ {scan.as_of_display()}")
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    for row in rows:
        table.add_row(
            f"{row.type}'s per kLOC",
            f"{row.fxtd_d.score:.2f}",
            f"{row.fxtd_d.grade}",
        )
    table.add_row(
        "Composite (weighted)",
        f"{composite.score:.2f}",
        composite.grade,
    )
    cli_console.print(table)
