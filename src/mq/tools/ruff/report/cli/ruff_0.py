"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Scan
from mq.tools.ruff.models import query

log = logging.getLogger(__name__)


def ruff_0(scan: Scan) -> None:
    row = query("0", scan=scan)
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}", show_header=False)
    table.add_column("_", style="bold magenta")
    table.add_column("_", style="bold magenta")
    table.add_row("Issues", f"{row.count:,d}")
    cli_console.print(table)
