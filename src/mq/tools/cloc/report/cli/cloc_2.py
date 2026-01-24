"""CLI report rendering obo 'cloc' tool for level 2."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.tools import format_int_or_percentage as fmt
from mq.tools.base import Scan
from mq.tools.cloc.models import query

log = logging.getLogger(__name__)


def cloc_2(args: Namespace, scan: Scan) -> None:
    rows, column_totals, grand_total = query(args, "2", scan=scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("File", footer="TOTAL")
    table.add_column("LOC", justify="right", footer=fmt(column_totals["lines_code"], False))
    table.add_column("Comments", justify="right", footer=fmt(column_totals["lines_comment"], False))
    table.add_column("Blank", justify="right", footer=fmt(column_totals["lines_blank"], False))
    table.add_column("TOTAL", justify="right", footer=fmt(grand_total, False))
    for row in rows:
        table.add_row(
            f"{row.directory}/{row.filename}",
            fmt(row.lines_code, False),
            fmt(row.lines_comment, False),
            fmt(row.lines_blank, False),
            fmt(row.lines_total, False),
        )
    cli_console.print(table)
