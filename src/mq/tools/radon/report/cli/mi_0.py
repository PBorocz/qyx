"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi

log = logging.getLogger(__name__)


def mi_0(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    row = query_mi(args, "0", scan)
    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row(
        "Composite Maintainability Score",
        f"{row.mi_mean:.2f}",
    )
    cli_console.print(table)
