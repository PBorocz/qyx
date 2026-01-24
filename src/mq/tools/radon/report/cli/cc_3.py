"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_cc


log = logging.getLogger(__name__)


def cc_3(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, "3", scan)
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
