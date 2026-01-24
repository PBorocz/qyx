"""CLI report rendering obo 'cloc' tool for level 2."""

import logging
from argparse import Namespace

from mq.cli import cli_table, cli_console
from mq.tools.base import Scan
from mq.tools.cloc.models import query

log = logging.getLogger(__name__)


def cloc_d(args: Namespace, scan: Scan) -> None:
    row = query(args, "d", scan=scan)

    table = cli_table(title=f"CLOC @ {scan.as_of_display()}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Explanation", justify="left")
    table.add_row(
        "File Density",
        f"{row.avg_lines_per_file.score:.2f}",
        row.avg_lines_per_file.grade,
        "Average LOC per File",
    )
    table.add_row(
        "Code Density",
        f"{row.code_density.score:.2f}",
        row.code_density.grade,
        "LOC / (LOC + Blanks)",
    )
    table.add_row(
        "Comment Ratio",
        f"{row.comment_ratio.score:.2f}",
        row.comment_ratio.grade,
        "Comments / (Comment + LOC)",
    )
    cli_console.print(table)
