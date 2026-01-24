"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Scan
from mq.tools.ruff.models import query

log = logging.getLogger(__name__)


def ruff_2(args: Namespace, scan: Scan) -> None:
    rows = query(args, "2", scan=scan)
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}")
    table.add_column("Rule")
    table.add_column("File [line]")
    table.add_column("Message")
    for row in rows:
        table.add_row(row.rule_code, f"{row.directory}/{row.filename} [{row.line}] ", row.message)
    cli_console.print(table)
