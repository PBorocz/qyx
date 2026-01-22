"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Scan
from mq.tools.ruff import get_ruff_rule_name
from mq.tools.ruff.models import query

log = logging.getLogger(__name__)


def ruff_1(scan: Scan) -> None:
    summary = query("0", scan=scan)
    results = query("1", scan=scan)
    show_footer = True if results else False
    table = cli_table(title=f"RUFF @ {scan.as_of_display()}", show_footer=show_footer)
    table.add_column("Rule", footer="TOTAL")
    table.add_column("Count", justify="center", footer=f"{summary.count:,}")
    table.add_column("Message")
    for result in results:
        rule_name = get_ruff_rule_name(result.rule_code)
        table.add_row(result.rule_code, f"{result.count:,d}", rule_name.title())
    cli_console.print(table)
