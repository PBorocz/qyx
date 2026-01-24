"""..."""

import logging
from argparse import Namespace

from mq.cli import cli_console, cli_table
from mq.tools.base import Project, Scan
from mq.tools.radon import COLORS
from mq.tools.radon.models import query_cc
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def cc_h(args: Namespace, project: Project = None, scan: Scan = None) -> None:
    timestamps, transposed, roc = query_cc(args, "h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)
    table = cli_table(title="RADON-CC Results Over Time")
    table.add_column("Complexity", justify="left")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:.2f}")

        t_value = ""
        roc_ = roc.get(entity_type, 0)
        if roc_ > 0.01:
            color = COLORS["negative"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        elif roc_ < -0.01:
            color = COLORS["positive"]
            t_value = f"[{color}][bold]{roc_:+.2f}%[/bold][/{color}]"
        else:
            t_value = ""

        t_row.append(t_value)

        table.add_row(*t_row)

    cli_console.print(table)
