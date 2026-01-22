"""CLI report rendering obo 'cloc' tool for level "h"."""

import logging

from mq.cli import cli_table, cli_console
from mq.tools.base import Project, Scan
from mq.tools.cloc.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def cloc_h(project: Project, scan: Scan) -> None:
    timestamps, rows, transposed, grand_totals, roc, adgs = query("h", project=project, scan=scan, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    if len(timestamps) <= 20:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("Metric", justify="left", footer="-")
        for timestamp in sorted(timestamps):
            table.add_column(
                timestamps_formatted[timestamp],
                justify="right",
                footer=str(grand_totals[timestamp]),
                footer_style="bold cyan",
            )
        if roc["grand_total"]:
            table.add_column("Delta", justify="left", footer=f"{roc['grand_total']:,.2f}%")

        for metric, dt_rows in transposed.items():
            row = [metric]
            for timestamp in sorted(timestamps):
                row.append(str(dt_rows[timestamp]))
            if roc[metric]:
                row.append(f"{roc[metric]:+.2f}%")
            table.add_row(*row)
    else:
        table = cli_table(title="CLOC Results Over Time", show_footer=True)
        table.add_column("", justify="left", footer="Mean Daily Growth")
        table.add_column("LOC", justify="right", footer=f"{adgs['total_code']:,.0f}")
        table.add_column("Comments", justify="right", footer=f"{adgs['total_comment']:,.0f}")
        table.add_column("Blank", justify="right", footer=f"{adgs['total_blank']:,.0f}")
        for row in rows:
            t_row = [
                timestamps_formatted[row.timestamp],
                f"{row.total_code:,d}",
                f"{row.total_comment:,d}",
                f"{row.total_blank:,d}",
            ]
            table.add_row(*t_row)

    cli_console.print(table)
