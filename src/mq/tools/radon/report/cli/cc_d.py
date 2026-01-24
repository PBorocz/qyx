"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_cc


log = logging.getLogger(__name__)


def cc_d(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows = query_cc(args, "d", project=project, scan=scan)
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
