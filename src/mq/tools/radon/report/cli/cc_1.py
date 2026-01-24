"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_cc

log = logging.getLogger(__name__)


def cc_1(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, "1", scan)
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
