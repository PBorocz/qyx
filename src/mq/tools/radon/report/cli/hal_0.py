"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_hal, RadonHal

log = logging.getLogger(__name__)


def hal_0(project: Project = None, scan: Scan = None) -> None:
    row = query_hal("0", scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for attr in RadonHal.attrs():
        table.add_row(attr.display, f"{getattr(row, attr.name):.2f}")
    cli_console.print(table)
