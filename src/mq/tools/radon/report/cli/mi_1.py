"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi

log = logging.getLogger(__name__)

RADON_SUB_TOOLS = ("raw", "mi", "hal", "cc")


def mi_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, mean_mi_mean, mean_mi_mean_footer, show_footer = query_mi(args, "1", scan)

    table = cli_table(title=f"RADON-MI @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Directory", justify="left", footer="Composite Maintainability")
    table.add_column("Maintainability Index", justify="right", footer=mean_mi_mean_footer)
    for row in rows:
        table.add_row(
            row.directory,
            f"{row.mi_mean:.2f}",
        )
    cli_console.print(table)
