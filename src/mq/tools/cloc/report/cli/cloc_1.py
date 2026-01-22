"""CLI report rendering obo 'cloc' tool for level 1."""

import logging

from mq.cli import cli_table, cli_console
from mq.tools import format_int_or_percentage as fmt
from mq.tools.base import Scan
from mq.tools.cloc.models import query

log = logging.getLogger(__name__)


def cloc_1(scan: Scan, percentage: bool = False) -> None:
    grand_total = query("0", scan=scan)
    detail_rows = query("1", scan=scan)
    table = cli_table(title=f"CLOC @ {scan.as_of_display()}", show_footer=True)
    table.add_column("Directory", justify="left", footer="TOTAL")

    footer = f"{grand_total.lines_code:,d} ({grand_total.lines_code_p:.1f}%)"
    table.add_column("LOC", justify="right", footer=footer)

    footer = f"{grand_total.lines_comment:,d} ({grand_total.lines_comment_p:.1f}%)"
    table.add_column("Comments", justify="right", footer=footer)

    footer = f"{grand_total.lines_blank:,d} ({grand_total.lines_blank_p:.1f}%)"
    table.add_column("Blank", justify="right", footer=footer)

    table.add_column("TOTAL", justify="right", footer=fmt(grand_total.lines_total, False))

    for result in detail_rows:
        table.add_row(
            result.directory,
            f"{result.lines_code:,d} ({result.lines_code_p:.1f}%)",
            f"{result.lines_comment:,d} ({result.lines_comment_p:.1f}%)",
            f"{result.lines_blank:,d} ({result.lines_blank_p:.1f}%)",
            f"{result.lines_total:,d} ({result.lines_total_p:.1f}%)",
        )
    cli_console.print(table)
