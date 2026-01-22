"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import RadonHal, query_hal

log = logging.getLogger(__name__)


def hal_1(project: Project = None, scan: Scan = None) -> None:
    rows, mean_means = query_hal("1", scan)
    table = cli_table(title=f"RADON-HAL @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="Mean")
    for attr in RadonHal.attrs():
        table.add_column(attr.display, justify="right", footer=f"{mean_means[attr.name]:.2f}")
    for row in rows:
        t_row = [row.directory]
        for attr in RadonHal.attrs():
            t_row.append(f"{getattr(row, attr.name):.2f}")
        table.add_row(*t_row)
    cli_console.print(table)
