"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import RadonHal, query_hal

log = logging.getLogger(__name__)


def hal_3(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    rows, means = query_hal(args, "3", scan)

    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", justify="left", footer="Mean")
    table.add_column("Name", justify="left")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{means[attr.name]:.2f}")
    for row in rows:
        t_row = [f"{row.directory}/{row.filename}", row.name]
        for attr in RadonHal.attrs():
            if attr.type == "float":
                value = f"{getattr(row, attr.name):.2f}"
            elif attr.type == "int":
                value = f"{getattr(row, attr.name):,d}"
            t_row.append(value)
        table.add_row(*t_row)
    cli_console.print(table)
