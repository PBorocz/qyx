"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_mi

log = logging.getLogger(__name__)


def mi_2(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, avg_footer, show_footer = query_mi(args, "2", scan)

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
