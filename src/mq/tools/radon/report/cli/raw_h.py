"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon.models import query_raw
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def raw_h(project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, rocs, roc_gt = query_raw("h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-RAW Results Over Time", show_footer=True)
    table.add_column("Metric", justify="left", footer="-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right", footer=f"{transposed['loc'][timestamp]:,d}")
    table.add_column("Delta", footer=f"{roc_gt:.2f}%")

    for metric, dt_rows in transposed.items():
        if metric == "loc":  # We already picked this up above!
            continue
        row = [metric]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:,d}")

        roc = rocs[metric]
        if -0.01 < roc < 0.01:
            t_value = ""
        else:
            t_value = f"{roc:+.2f}%"

        row.append(t_value)
        table.add_row(*row)

    cli_console.print(table)
