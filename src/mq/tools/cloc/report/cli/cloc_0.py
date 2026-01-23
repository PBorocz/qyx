"""CLI report rendering obo 'cloc' tool - level 0."""

import logging

from mq.cli import cli_table, cli_console
from mq.tools.base import Scan
from mq.tools.cloc.models import query

log = logging.getLogger(__name__)


def cloc_0(scan: Scan) -> None:
    result = query("0", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}")
    table.add_column("LOC", justify="center")
    table.add_column("Comments", justify="center")
    table.add_column("Blanks", justify="center")
    table.add_column("TOTAL", justify="center")
    table.add_row(
        f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
        f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
        f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
        f"{result.lines_total:,d}",
    )
    cli_console.print(table)
