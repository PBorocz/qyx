"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon import COLORS
from mq.tools.radon.models import query_hal
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def hal_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, rocs = query_hal(args, "h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-HAL Results Over Time")
    table.add_column("Metric", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for attr, dt_rows in transposed.items():
        t_row = [attr]
        for timestamp in sorted(timestamps):
            t_row.append(f"{dt_rows[timestamp]:.2f}")

        roc = rocs[attr]
        t_value = ""
        if roc > 0.01:
            color = COLORS["positive"]
            t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"

        elif roc < -0.01:
            color = COLORS["negative"]
            t_value = f"[{color}][bold]{roc:+.1f}%[/bold][/{color}]"

        t_row.append(t_value)
        table.add_row(*t_row)

    cli_console.print(table)
