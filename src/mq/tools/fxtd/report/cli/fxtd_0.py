"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Scan
from mq.tools.fxtd.models import query

log = logging.getLogger(__name__)


def fxtd_0(args: Namespace, scan: Scan) -> None:
    results = query(args, "0", scan=scan)
    grand_total = sum([result.count for result in results])
    show_footer = True if results else False
    table = cli_table(title=f"FXTD @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Type", footer="TOTAL")
    table.add_column("Count", justify="center", footer=f"{grand_total:,}")
    for result in results:
        table.add_row(result.type, f"{result.count:,d}")
    cli_console.print(table)
