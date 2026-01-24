"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon import COLORS
from mq.tools.radon.models import query_mi
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def mi_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, roc = query_mi(args, "h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-MI Results Over Time")
    table.add_column("Metric")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta", justify="right")

    for metric, dt_rows in transposed.items():
        row = ["Maintainability Index"]
        for timestamp in sorted(timestamps):
            row.append(f"{dt_rows[timestamp]:.2f}")

        if roc > 0.01:
            color = COLORS["positive"]
        elif roc < -0.01:
            color = COLORS["negative"]
        else:
            color = COLORS["neutral"]

        row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*row)
    cli_console.print(table)
