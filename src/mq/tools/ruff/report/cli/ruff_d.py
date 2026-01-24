"""CLI report rendering obo 'ruff' tool for level d or derived data."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.tools.base import Project, Scan
from mq.tools.ruff.models import query

log = logging.getLogger(__name__)


def ruff_d(args: Namespace, project: Project, scan: Scan) -> None:
    row = query(args, "d", project=project, scan=scan)

    table = cli_table(title=f"RUFF @ {scan.as_of_display()}")
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    table.add_row(
        "Raw Ruff Issues per kLOC",
        f"{row.violations_per_kloc.score:.0f}",
        f"{row.violations_per_kloc.grade}",
    )
    table.add_row(
        "Weighted Ruff Issues per kLOC",
        f"{row.weighted_violations_per_kloc.score:.0f}",
        f"{row.weighted_violations_per_kloc.grade}",
    )
    cli_console.print(table)
